-- Anime4K v4 profile switching for mpv, for people who do not have their own
-- mpv setup. The shader chain is switched at runtime, so nothing has to be
-- restarted and no input.conf is touched.
--
-- It works with the stock OSC and with ModernZ. ModernZ has no plugin API (it
-- only accepts the script messages osc-show/osc-hide/osc-visibility), so there
-- is no button inside its UI; the entry points are the keys below and an OSD
-- menu on Ctrl+a.
--
-- Keys
--   Ctrl+1..6  profile A, B, C, A+A, B+B, C+A
--   Ctrl+0     Anime4K off
--   Ctrl+a     OSD menu (profiles, off, HQ toggle)
--
-- Install: copy to ~/.config/mpv/scripts/, or
--   mpv --script=/path/to/aniworld-anime4k.lua \
--       --script-opts=aniworld-anime4k-shaders_dir=/path/to/Anime4K/shaders
--
-- shaders_dir is the directory that contains Restore/, Upscale/ and
-- Upscale+Denoise/ from an Anime4K release.

local mp = require 'mp'
local msg = require 'mp.msg'
local utils = require 'mp.utils'
local options = require 'mp.options'

local opts = {
    -- Where the .glsl files live (required for anything to happen).
    shaders_dir = "",
    -- Profile applied when a file loads: a, b, c, a+a, b+b, c+a.
    mode = "a",
    -- Use the larger VL/UL networks instead of M/S (slower, cleaner).
    hq = false,
    -- Set to "no" to start with Anime4K off.
    enabled = true,
}

options.read_options(opts, "aniworld-anime4k")

-- A step is either a fixed shader or "family:size", following the official v4
-- templates (the same chains aniworld_cli uses for --anime4k).
local fixed = {
    clamp = "Restore/Anime4K_Clamp_Highlights.glsl",
    adp2 = "Upscale/Anime4K_AutoDownscalePre_x2.glsl",
    adp4 = "Upscale/Anime4K_AutoDownscalePre_x4.glsl",
}

local families = {
    restore = "Restore/Anime4K_Restore_CNN_%s.glsl",
    restore_soft = "Restore/Anime4K_Restore_CNN_Soft_%s.glsl",
    upscale = "Upscale/Anime4K_Upscale_CNN_x2_%s.glsl",
    upscale_denoise = "Upscale+Denoise/Anime4K_Upscale_Denoise_CNN_x2_%s.glsl",
}

-- hq moves every CNN two sizes up, as --anime4k-hq does in the CLI.
local hq_sizes = { S = "M", M = "VL", L = "UL" }

local profiles = {
    {
        id = "a",
        label = "A (1080p)",
        steps = { "clamp", "restore:M", "upscale:M", "adp2", "adp4", "upscale:S" },
    },
    {
        id = "b",
        label = "B (720p)",
        steps = { "clamp", "restore_soft:M", "upscale:M", "adp2", "adp4", "upscale:S" },
    },
    {
        id = "c",
        label = "C (480p)",
        steps = { "clamp", "upscale_denoise:M", "adp2", "adp4", "upscale:S" },
    },
    {
        id = "a+a",
        label = "A+A (1080p, two passes)",
        steps = { "clamp", "restore:M", "upscale:M", "restore:S", "adp2", "adp4", "upscale:S" },
    },
    {
        id = "b+b",
        label = "B+B (720p, two passes)",
        steps = { "clamp", "restore_soft:M", "upscale:M", "adp2", "adp4", "restore_soft:S", "upscale:S" },
    },
    {
        id = "c+a",
        label = "C+A (480p, two passes)",
        steps = { "clamp", "upscale_denoise:M", "adp2", "adp4", "restore:S", "upscale:S" },
    },
}

local by_id = {}
for _, profile in ipairs(profiles) do
    by_id[profile.id] = profile
end

-- Relative shader paths for a profile, in processing order.
local function expand(steps, hq)
    local paths = {}
    for _, step in ipairs(steps) do
        local family, size = step:match("^([%w_]+):?(%w*)$")
        if fixed[family] then
            paths[#paths + 1] = fixed[family]
        else
            local pattern = families[family]
            if not pattern then
                error("unknown Anime4K step '" .. step .. "'")
            end
            if hq then
                size = hq_sizes[size] or size
            end
            paths[#paths + 1] = pattern:format(size)
        end
    end
    return paths
end

local state = { profile = nil }

local function shader_dir()
    local dir = opts.shaders_dir
    if dir == "" then
        return nil
    end
    return dir:gsub("/+$", "")
end

local function missing_shader(paths)
    for _, path in ipairs(paths) do
        if not utils.file_info(path) then
            return path
        end
    end
    return nil
end

local function set_chain(paths)
    mp.set_property_native("glsl-shaders", paths)
end

-- Apply `id` (or turn Anime4K off when id is nil). Quiet skips the OSD, which
-- is what the automatic start-of-file apply wants.
local function apply(id, quiet)
    if not id then
        set_chain({})
        state.profile = nil
        if not quiet then
            mp.osd_message("Anime4K: off", 2)
        end
        return
    end

    local profile = by_id[id]
    if not profile then
        msg.warn("unknown profile '" .. tostring(id) .. "'")
        return
    end

    local dir = shader_dir()
    if not dir then
        if not quiet then
            mp.osd_message("Anime4K: set aniworld-anime4k-shaders_dir", 3)
        end
        msg.warn("aniworld-anime4k: shaders_dir is not set")
        return
    end

    local paths = expand(profile.steps, opts.hq)
    for i, path in ipairs(paths) do
        paths[i] = dir .. "/" .. path
    end

    local missing = missing_shader(paths)
    if missing then
        msg.error("aniworld-anime4k: missing shader " .. missing)
        if not quiet then
            mp.osd_message("Anime4K: shaders not found in " .. dir, 3)
        end
        return
    end

    set_chain(paths)
    state.profile = profile.id
    if not quiet then
        mp.osd_message("Anime4K: " .. profile.label .. (opts.hq and " [HQ]" or ""), 2)
    end
end

local function menu()
    if not mp.input then
        -- mpv older than 0.38: no menu, so cycle instead.
        local ids = {}
        for _, profile in ipairs(profiles) do
            ids[#ids + 1] = profile.id
        end
        local next_index = 1
        for i, id in ipairs(ids) do
            if id == state.profile then
                next_index = i + 1
            end
        end
        apply(ids[next_index] or ids[1])
        return
    end

    local items = {}
    local actions = {}
    for _, profile in ipairs(profiles) do
        items[#items + 1] = (profile.id == state.profile and "* " or "  ") .. profile.label
        actions[#actions + 1] = profile.id
    end
    items[#items + 1] = (state.profile == nil and "* " or "  ") .. "Off"
    actions[#actions + 1] = false
    items[#items + 1] = "HQ shaders (VL/UL): " .. (opts.hq and "on" or "off")
    actions[#actions + 1] = "hq"

    local default_item = 1
    for i, action in ipairs(actions) do
        if action == state.profile then
            default_item = i
        end
    end

    mp.input.select({
        prompt = "Anime4K profile",
        items = items,
        default_item = default_item,
        submit = function(id)
            local action = actions[id]
            if action == "hq" then
                opts.hq = not opts.hq
                if state.profile then
                    apply(state.profile)
                else
                    mp.osd_message("Anime4K: HQ " .. (opts.hq and "on" or "off"), 2)
                end
            elseif action then
                apply(action)
            else
                apply(nil)
            end
        end,
    })
end

local started = false

mp.register_event("file-loaded", function()
    if started then
        return
    end
    started = true
    if opts.enabled then
        apply(opts.mode, true)
    end
end)

local keys = { "1", "2", "3", "4", "5", "6" }
for i, key in ipairs(keys) do
    local profile = profiles[i]
    mp.add_key_binding("Ctrl+" .. key, "profile-" .. profile.id, function()
        apply(profile.id)
    end)
end

mp.add_key_binding("Ctrl+0", "off", function()
    apply(nil)
end)

mp.add_key_binding("Ctrl+a", "menu", menu)

mp.register_script_message("aniworld-anime4k-mode", function(id)
    if id == "off" then
        apply(nil)
    else
        apply(id)
    end
end)

mp.register_script_message("aniworld-anime4k-menu", menu)

-- Loaded by mpv as a script; the table is here so the profiles can be tested
-- without a player.
return {
    profiles = profiles,
    by_id = by_id,
    expand = expand,
}
