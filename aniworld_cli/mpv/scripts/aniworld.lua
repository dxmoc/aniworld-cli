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

local menu = { open = false, kind = nil }
-- Two overlays, not one event: inside a single ASS event any text after a
-- drawing is laid out *after the drawing's bounding box*, so a "box then text"
-- event puts the text outside the box and the fill can pick up the text colour.
-- A separate background layer has neither problem.
local panel = mp.create_osd_overlay("ass-events")
panel.z = 99
local overlay = mp.create_osd_overlay("ass-events")
overlay.z = 100

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
local C_SEL = "&H00FFA032&"  -- ModernZ's accent orange
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

-- Pixel height of one row, so the panel box ends just below the last line.
local function row_height(row)
    local height = LINE
    if hint_of(row) ~= "" or row.recommended then height = height + HINT_LINE end
    return height
end

local function group(title, rows, mark, offset)
    offset = offset or 0
    local out = { "{\\fs26\\b1\\c" .. C_TITLE .. "}" .. esc(title) .. "{\\b0}\\N" }
    for i, row in ipairs(rows) do
        local sel = (row.token == mark)
        local key = offset + i
        -- Rows beyond the ninth key are drawn dimmed: the key does nothing.
        out[#out + 1] = string.format(
            "{\\fs24\\c%s}%s %s  %s{\\c}\\N",
            sel and C_SEL or (key <= KEYS and C_TEXT or C_DIM),
            sel and "●" or "○",
            key <= KEYS and tostring(key) or "-",
            esc(row.label)
        )
        local hint = hint_of(row)
        if hint ~= "" or row.recommended then
            out[#out + 1] = "{\\fs19\\c" .. C_DIM .. "}      " .. esc(hint)
                .. (row.recommended
                    and "{\\c" .. C_SEL .. "}   recommended for this stream" or "")
                .. "{\\c}\\N"
        end
    end
    return table.concat(out)
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

local function render()
    local groups = groups_for(menu.kind)
    local total = #rows_of(menu.kind)

    local parts, height = {}, 0
    local offset = 0
    for _, g in ipairs(groups) do
        parts[#parts + 1] = group(g[1], g[2], g[3], offset)
        offset = offset + #g[2]
        height = height + LINE             -- group title
        for _, row in ipairs(g[2]) do
            height = height + row_height(row)
        end
    end
    local body = table.concat(parts, "\\N")

    local head = "{\\fs20\\c" .. C_DIM .. "}" .. esc(STATE.episode or "")
        .. "{\\c}\\N"
    local foot = "{\\fs18\\c" .. C_DIM .. "}1-" .. math.min(total, KEYS) .. " pick"
        .. "   Esc close"
        .. (STATE.busy and "   resolving..." or "") .. "{\\c}"

    -- Hinted menus need room for the explanation and the recommendation note.
    local wide = false
    for _, g in ipairs(groups) do
        for _, row in ipairs(g[2]) do
            if hint_of(row) ~= "" then wide = true end
        end
    end
    local W = wide and 860 or 620
    local H = 16 + 28 + height + 30

    panel.data = string.format(
        "{\\an7\\pos(40,40)\\p1\\bord0\\shad0\\1c&H101010&\\1a&H40&}"
            .. "m 0 0 l %d 0 %d %d 0 %d{\\p0}",
        W, W, H, H
    )
    panel:update()

    overlay.data = "{\\an7\\pos(58,54)}" .. head .. body .. "\\N" .. foot
    overlay:update()
end

local function close()
    menu.open = false
    menu.kind = nil
    overlay:remove()
    panel:remove()
end

local function open(kind)
    if STATE.busy then return end
    menu.open = true
    menu.kind = kind
    render()
end

local function send(action, value)
    mp.commandv("script-message", "aniworld-cmd", action, tostring(value or ""))
end

local function pick(index)
    local row = rows_of(menu.kind)[index]
    if not row then return end
    local action = row.action or menu.kind
    close()
    send(action, row.token)
end

mp.add_key_binding(nil, "menu", function() open("all") end)
mp.add_key_binding(nil, "menu-language", function() open("language") end)
mp.add_key_binding(nil, "menu-shaders", function() open("shader") end)
mp.add_key_binding(nil, "menu-quality", function() open("quality") end)

for i = 1, 9 do
    mp.add_key_binding(tostring(i), "pick-" .. i, function()
        if menu.open then pick(i) end
    end, { repeatable = false })
end
mp.add_key_binding("ESC", "close-menu", function()
    if menu.open then close() end
end)

-- The CLI answers with a fresh state after every change.
mp.register_script_message("state", function(json)
    local ok, parsed = pcall(utils.parse_json, json)
    if ok and type(parsed) == "table" then
        merge(STATE, parsed)
        if menu.open then render() end
    end
end)

mp.register_script_message("osd", function(text, duration)
    mp.osd_message(text, tonumber(duration) or 2.5)
end)

mp.register_event("end-file", function()
    if menu.open then close() end
end)
