-- aniworld-cli in-player controls.
--
-- This script only draws menus and forwards choices. Everything that needs the
-- network (re-resolving a language/hoster/quality) lives in the CLI, which
-- answers over mpv's JSON IPC socket. The app hands us its state through the
-- environment, because --script-opts cannot carry paths with commas and
-- mp.get_script_directory() is nil for scripts auto-loaded from a config dir.

local mp = require "mp"
local msg = require "mp.msg"
local utils = require "mp.utils"

-- Menu labels live here, not in i18n.py: the CLI's strings never reach a
-- script running inside mpv. Ordered as shown.
local STATE = {
    lang = nil,
    quality = nil,
    shader = nil,
    langs = {},      -- { {token="ger-dub", label="German dub"}, ... }
    qualities = {},  -- { {token="720", label="720p"}, ... }
    shaders = {},    -- { {token="a", label="Mode A (HQ)"}, ... }
    episode = nil,
    hoster = nil,
    busy = false,
}

local menu = { open = false, kind = nil, hover = nil }

-- Gap under the dimmed episode line before the first group title.
local HEAD_LINE = 27
local hits = {}
local menu_keys_on = false

-- Defined further down, but the panel lifecycle needs them in either order.
local close, open, pick, bind_menu_keys
-- Three overlays: box, hover bar, text. Inside a single ASS event any text after
-- a drawing is laid out *after the drawing's bounding box*, so a "box then text"
-- event puts the text outside the box and the fill picks up the text colour.
--
-- The text overlay carries *one event per line*, separated by newlines. libass
-- ignores a second \pos inside the same event and just flows the text at its
-- natural line height (~24px for fs24), whatever the coordinates say -- that is
-- why the click bands and the visible rows drifted apart. Separate events honour
-- every \pos exactly, so the bands are derived from the same y values.
local panel = mp.create_osd_overlay("ass-events")
panel.z = 98
local overlay = mp.create_osd_overlay("ass-events")
overlay.z = 100
-- The highlight for the row under the mouse. Its own overlay because one ASS
-- event can only carry one painting, and this has to sit under the text.
local hbar = mp.create_osd_overlay("ass-events")
hbar.z = 99
-- Pin the drawing canvas. Without this mpv derives a resolution from the window
-- size, so the same ASS coordinates land in different places in a narrow and a
-- wide window -- and a mouse position could not be mapped back onto them.
for _, o in ipairs({panel, hbar, overlay}) do
    o.res_x, o.res_y = 1280, 720
end

local function env_json(name)
    local raw = os.getenv(name)
    if not raw or raw == "" then return nil end
    local ok, parsed = pcall(utils.parse_json, raw)
    if ok and type(parsed) == "table" then return parsed end
    msg.warn("cannot parse " .. name)
    return nil
end

local function merge(target, source)
    if type(source) ~= "table" then return end
    for k, v in pairs(source) do target[k] = v end
end

merge(STATE, env_json("ANIWORLD_MPV_STATE") or {})

-- ASS colours are BGR.
local C_TITLE = "&H00E8E8E8&"
local C_TEXT = "&H00C8C8C8&"
local C_SEL = "&H00FFA032&"  -- ModernZ accent (#32A0FF, ASS is BGR)
local C_DIM = "&H00909090&"

local function esc(text)
    return tostring(text or ""):gsub("\\", ""):gsub("{", "("):gsub("}", ")")
end

-- Only a single 1-9 row range exists, so a menu must never show more than nine
-- selectable rows. "all" therefore stays at language + quality (6 rows) and the
-- shader list gets its own menu (7 rows), instead of one 13-row list whose last
-- four entries would be unreachable.
local KEYS = 9

-- Panel layout. A hint line is smaller than a label line, and the box is sized
-- from these numbers, so they have to match what is drawn.
local LINE = 31
local HINT_LINE = 26

-- Rows may carry a one-line explanation (the shader presets do). It is drawn
-- dimmed underneath the label: a bare "Mode B" says nothing about what a mode
-- costs or when it is the right pick.
local function hint_of(row)
    return row.hint or ""
end


-- Every line is placed with an explicit \pos, at the same y the click bands use.
-- Letting ASS flow the lines would leave the bands guessing at font metrics.
local PAD_X, PAD_Y = 58, 54

-- The background box lives in its own overlay, 18px left of and above the first
-- line, and ends 22px below the last one.
local BOX_X, BOX_Y = 40, 40

local function draw_panel(width, height)
    panel.data = string.format(
        "{\\an7\\pos(%d,%d)\\p1\\bord0\\shad0\\1c&H101010&\\1a&H40&}"
            .. "m 0 0 l %d 0 %d %d 0 %d{\\p0}",
        BOX_X, BOX_Y, width, width, height, height
    )
    panel:update()
end

local function text_line(x, y, style, body)
    return string.format("{\\an7\\pos(%d,%d)%s}%s", x, y, style, body)
end

-- A translucent bar behind the row under the mouse. Bold text alone is far too
-- subtle at this font size to read as "you can click this".
local function draw_hover_bar(where, width)
    local band = hits[menu.hover]
    if not where or not band then
        hbar:remove()
        return
    end
    local x, w = BOX_X + 8, width - 16
    local y, h = band.top - 5, (band.bottom - band.top) + 4
    hbar.data = string.format(
        "{\\an7\\pos(%d,%d)\\p1\\bord0\\shad0\\1c&HFFA032&\\1a&H60&}"
            .. "m 0 0 l %d 0 %d %d 0 %d{\\p0}",
        x, y, w, w, h, h
    )
    hbar:update()
end

-- Shown by Alt+k and by the keyboard button. Keep in sync with input.conf and the
-- OSC buttons: this panel is the only place a user can discover them. The second
-- group is plain mpv, for people who have never used a keyboard-driven player.
local SHORTCUTS = {
    { "aniworld-cli", {
        { "Alt+s", "language and quality" },
        { "Alt+l", "language" },
        { "Alt+q", "quality" },
        { "Alt+u", "Anime4K preset" },
        { "Alt+k", "this list" },
        { "1-9",   "pick a row (or click it)" },
        { "Esc",   "close" },
    } },
    { "player", {
        { "Space",      "pause / play" },
        { "Left/Right", "seek 5 seconds" },
        { "Up/Down",    "seek 1 minute" },
        { "f",          "fullscreen" },
        { "m",          "mute" },
        { "9",          "volume down" },
        { "0",          "volume up" },
        { "[ / ]",      "play slower / faster" },
        { "q",          "quit" },
    } },
}

-- The keybind list is by far the longest thing this script draws. As one column
-- it reaches under the OSC, where the last rows are unreadable, so each group
-- gets its own column and the whole panel stays in the upper half of the screen.
local SHORTCUT_COL = 470

local function shortcuts_overlay()
    local out = {}
    out[#out + 1] = text_line(PAD_X, PAD_Y, "\\fs26\\b1\\c" .. C_TITLE,
        "Keybinds{\\b0\\c}")
    local top = PAD_Y + LINE
    -- The lowest point any column reaches, so the box fits the tallest one.
    local bottom = top
    for i, group_def in ipairs(SHORTCUTS) do
        local x = PAD_X + (i - 1) * SHORTCUT_COL
        local y = top
        out[#out + 1] = text_line(x, y, "\\fs22\\b1\\c" .. C_TITLE,
            esc(group_def[1]) .. "{\\b0\\c}")
        y = y + LINE
        for _, entry in ipairs(group_def[2]) do
            out[#out + 1] = text_line(x, y, "\\fs24\\c" .. C_SEL,
                esc(entry[1]) .. "{\\c" .. C_TEXT .. "}   " .. esc(entry[2]) .. "{\\c}")
            y = y + LINE
        end
        if y > bottom then bottom = y end
    end
    out[#out + 1] = text_line(PAD_X, bottom, "\\fs18\\c" .. C_DIM, "Esc close{\\c}")

    local columns = math.max(#SHORTCUTS, 1)
    draw_panel(SHORTCUT_COL * columns - 30, (bottom + 22) - 40)
    hbar:remove()
    overlay.data = table.concat(out, "\n")
    overlay:update()
end

local function groups_for(kind)
    if kind == "language" then return { { "Language", STATE.langs, STATE.lang } } end
    if kind == "quality" then return { { "Quality", STATE.qualities, STATE.quality } } end
    if kind == "shader" then return { { "Shaders", STATE.shaders, STATE.shader } } end
    if kind == "all" then
        return {
            { "Language", STATE.langs, STATE.lang },
            { "Quality", STATE.qualities, STATE.quality },
        }
    end
    return {}
end

-- Flatten the groups a menu shows, in display order, so a numeric key always
-- picks the row that is drawn at that position.
local function rows_of(kind)
    local out = {}
    for _, g in ipairs(groups_for(kind)) do
        for _, row in ipairs(g[2]) do out[#out + 1] = row end
    end
    return out
end

local function render_impl()
    if menu.kind == "shortcuts" then
        shortcuts_overlay()
        return
    end
    local groups = groups_for(menu.kind)
    local total = #rows_of(menu.kind)

    local out = {}
    local y = PAD_Y
    local index = 0
    local wide = false

    out[#out + 1] = text_line(PAD_X, y, "\\fs20\\c" .. C_DIM,
        esc(STATE.episode or "") .. "{\\c}")
    y = y + HEAD_LINE

    hits = {}
    for _, g in ipairs(groups) do
        out[#out + 1] = text_line(PAD_X, y, "\\fs26\\b1\\c" .. C_TITLE,
            esc(g[1]) .. "{\\b0\\c}")
        y = y + LINE
        for _, row in ipairs(g[2]) do
            index = index + 1
            local sel = (row.token == g[3])
            local hot = (index == menu.hover)
            local top = y
            -- The row under the mouse is bold and accented; the selected one
            -- keeps its filled marker regardless.
            out[#out + 1] = text_line(PAD_X, y,
                string.format("\\fs24%s\\c%s", hot and "\\b1" or "",
                    hot and C_TITLE or (sel and C_SEL or (index <= KEYS and C_TEXT or C_DIM))),
                string.format("%s %s  %s{\\c\\b0}",
                    sel and "●" or "○",
                    index <= KEYS and tostring(index) or "-",
                    esc(row.label)))
            y = y + LINE

            local hint = hint_of(row)
            if hint ~= "" or row.recommended then
                if hint ~= "" then wide = true end
                out[#out + 1] = text_line(PAD_X + 30, y, "\\fs19\\c" .. C_DIM,
                    esc(hint) .. (row.recommended
                        and ("{\\c" .. C_SEL .. "}   recommended for this stream") or "")
                        .. "{\\c}")
                y = y + HINT_LINE
            end
            hits[#hits + 1] = { top = top, bottom = y, index = index }
        end
        y = y + 8
    end

    out[#out + 1] = text_line(PAD_X, y, "\\fs18\\c" .. C_DIM,
        "1-" .. math.min(total, KEYS) .. " or click to pick"
            .. "   Esc close" .. (STATE.busy and "   resolving..." or "") .. "{\\c}")

    local W = wide and 860 or 620
    draw_panel(W, (y + 22) - 40)
    draw_hover_bar(menu.hover, W)
    overlay.data = table.concat(out, "\n")
    overlay:update()
end

-- mpv terminates a script for good on an uncaught Lua error, and every later
-- button press then fails with "can't find script". A drawing bug must not take
-- the whole integration down with it, so the panel is drawn inside pcall.
local function render()
    local ok, err = pcall(render_impl)
    if not ok then msg.error("render: " .. tostring(err)) end
end

function close()
    menu.open = false
    menu.kind = nil
    menu.hover = nil
    overlay:remove()
    panel:remove()
    hbar:remove()
    bind_menu_keys(false)
end

function open(kind)
    if STATE.busy then return end
    menu.open = true
    menu.kind = kind
    menu.hover = nil
    bind_menu_keys(true)
    render()
end

local function send(action, value)
    mp.commandv("script-message", "aniworld-cmd", action, tostring(value or ""))
end

-- The A4K button shows a crossed-out icon while no preset is active, so the
-- state it reads has to be published as an mpv property. ModernZ repaints the
-- button when this changes (custom_button1_toggle_property).
local function publish_state()
    mp.set_property_native("user-data/aniworld/shaders-off", STATE.shader == "off")
end

-- What "on" means when the user toggles back: the preset that was active
-- before, else the one the CLI recommends for this stream.
local last_on = nil

local function recommended_token()
    for _, row in ipairs(STATE.shaders or {}) do
        if row.recommended then return row.token end
    end
    return nil
end

local function apply(kind, token)
    STATE[kind] = token
    publish_state()
    send(kind, token)
end

-- Left click on A4K: on <-> off, without opening anything.
local function toggle_shaders()
    if STATE.busy then return end
    if STATE.shader == "off" then
        apply("shader", last_on or recommended_token() or "a")
    else
        last_on = STATE.shader
        apply("shader", "off")
    end
end

function pick(index)
    local row = rows_of(menu.kind)[index]
    if not row then return end
    local action = row.action or menu.kind
    if action == "shader" and row.token ~= "off" then last_on = row.token end
    close()
    apply(action, row.token)
end

-- Which row sits under this mouse position, or nil. The bands come from the last
-- render, so a click always lands on what is actually drawn.

-- Mouse positions arrive in OSD pixels; the panel is drawn on the pinned
-- 1280x720 canvas that mpv scales into the same area. osd-dimensions is the
-- pixel size of that area, so it is the scale factor -- the same conversion
-- ModernZ's get_virt_scale_factor() does for its buttons.
local function to_canvas(x, y)
    local dim = mp.get_property_native("osd-dimensions") or {}
    local width, height = dim.w, dim.h
    if not width or width == 0 then
        width, height = mp.get_osd_size()      -- before the first frame
    end
    if not width or width == 0 or not height or height == 0 then return nil end
    return x * 1280 / width, y * 720 / height
end

-- Which row sits under this mouse position, or nil. The bands are the rows as
-- they were drawn, so what is hit is what is on screen.
local function row_at(mouse_x, mouse_y)
    if menu.kind == "shortcuts" then return nil end
    local x, y = to_canvas(mouse_x, mouse_y)
    if not x then return nil end
    if x < 40 or x > 940 then return nil end
    for _, band in ipairs(hits) do
        if y >= band.top and y < band.bottom then return band.index end
    end
    return nil
end

local function click()
    if not menu.open then return end
    local pos = mp.get_property_native("mouse-pos")
    local index = pos and row_at(pos.x, pos.y)
    if index then
        pick(index)
    else
        close()          -- a click anywhere else dismisses the panel
    end
end

-- Digits and the left button only mean something while a menu is up. Taking
-- them temporarily keeps 1-9 working as mpv's own keys the rest of the time
-- (9 is volume up, 1 and 2 adjust contrast).
function bind_menu_keys(on)
    if on == menu_keys_on then return end
    menu_keys_on = on
    if on then
        mp.add_forced_key_binding("MBTN_LEFT", "pick-click", click)
        for i = 1, 9 do
            mp.add_forced_key_binding(tostring(i), "pick-" .. i, function() pick(i) end)
        end
    else
        mp.remove_key_binding("pick-click")
        for i = 1, 9 do mp.remove_key_binding("pick-" .. i) end
    end
end

-- Hover feedback: a row under the cursor is drawn in bold accent.
mp.observe_property("mouse-pos", "native", function(_, pos)
    if not menu.open or not pos then return end
    local index = row_at(pos.x, pos.y)
    if index ~= menu.hover then
        menu.hover = index
        render()
    end
end)

mp.add_key_binding(nil, "menu", function() open("all") end)
mp.add_key_binding(nil, "menu-language", function() open("language") end)
mp.add_key_binding(nil, "menu-shaders", function() open("shader") end)
mp.add_key_binding(nil, "toggle-shaders", toggle_shaders)
mp.add_key_binding(nil, "menu-quality", function() open("quality") end)
mp.add_key_binding(nil, "menu-shortcuts", function() open("shortcuts") end)


mp.add_key_binding("ESC", "close-menu", function()
    if menu.open then close() end
end)

-- The CLI answers with a fresh state after every change.
mp.register_script_message("state", function(json)
    local ok, parsed = pcall(utils.parse_json, json)
    if ok and type(parsed) == "table" then
        merge(STATE, parsed)
        if STATE.shader and STATE.shader ~= "off" then last_on = STATE.shader end
        publish_state()
        if menu.open then render() end
    end
end)

mp.register_script_message("osd", function(text, duration)
    mp.osd_message(text, tonumber(duration) or 2.5)
end)

mp.register_event("end-file", function()
    if menu.open then close() end
end)

-- The OSC button starts out reflecting whatever preset the CLI picked.
publish_state()
