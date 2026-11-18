-- Checks mpv/aniworld-anime4k.lua without a player: the shader chains it builds
-- and the keys it binds. Run with `lua tests/mpv/aniworld-anime4k_test.lua`, or
-- pass the script path as the first argument.
--
-- The expected chains are the official Anime4K v4 (fast) templates, the same
-- ones aniworld_cli uses for --anime4k.

local script_path = arg[1] or "mpv/aniworld-anime4k.lua"

local calls = { props = {}, keys = {}, messages = {} }

package.preload["mp"] = function()
    return {
        osd_message = function(text)
            table.insert(calls.messages, text)
        end,
        add_key_binding = function(key, name)
            table.insert(calls.keys, key .. "/" .. name)
        end,
        register_event = function() end,
        register_script_message = function() end,
        set_property_native = function(property, value)
            table.insert(calls.props, { property = property, value = value })
        end,
    }
end

package.preload["mp.msg"] = function()
    return { warn = function() end, error = function() end, info = function() end }
end

package.preload["mp.utils"] = function()
    return { file_info = function(path) return { path = path } end }
end

package.preload["mp.options"] = function()
    return { read_options = function() end }
end

local script = dofile(script_path)

local shader = {
    clamp = "Restore/Anime4K_Clamp_Highlights.glsl",
    adp2 = "Upscale/Anime4K_AutoDownscalePre_x2.glsl",
    adp4 = "Upscale/Anime4K_AutoDownscalePre_x4.glsl",
    ["restore:S"] = "Restore/Anime4K_Restore_CNN_S.glsl",
    ["restore:M"] = "Restore/Anime4K_Restore_CNN_M.glsl",
    ["restore:VL"] = "Restore/Anime4K_Restore_CNN_VL.glsl",
    ["restore_soft:S"] = "Restore/Anime4K_Restore_CNN_Soft_S.glsl",
    ["restore_soft:M"] = "Restore/Anime4K_Restore_CNN_Soft_M.glsl",
    ["restore_soft:VL"] = "Restore/Anime4K_Restore_CNN_Soft_VL.glsl",
    ["upscale:S"] = "Upscale/Anime4K_Upscale_CNN_x2_S.glsl",
    ["upscale:M"] = "Upscale/Anime4K_Upscale_CNN_x2_M.glsl",
    ["upscale:VL"] = "Upscale/Anime4K_Upscale_CNN_x2_VL.glsl",
    ["upscale_denoise:M"] = "Upscale+Denoise/Anime4K_Upscale_Denoise_CNN_x2_M.glsl",
    ["upscale_denoise:VL"] = "Upscale+Denoise/Anime4K_Upscale_Denoise_CNN_x2_VL.glsl",
}

local expected = {
    ["a"] = { "clamp", "restore:M", "upscale:M", "adp2", "adp4", "upscale:S" },
    ["b"] = { "clamp", "restore_soft:M", "upscale:M", "adp2", "adp4", "upscale:S" },
    ["c"] = { "clamp", "upscale_denoise:M", "adp2", "adp4", "upscale:S" },
    ["a+a"] = { "clamp", "restore:M", "upscale:M", "restore:S", "adp2", "adp4", "upscale:S" },
    ["b+b"] = { "clamp", "restore_soft:M", "upscale:M", "adp2", "adp4", "restore_soft:S", "upscale:S" },
    ["c+a"] = { "clamp", "upscale_denoise:M", "adp2", "adp4", "restore:S", "upscale:S" },
}

-- hq moves every CNN two sizes up, like --anime4k-hq in the CLI.
local hq_size = { S = "M", M = "VL", L = "UL" }

local failures = 0
local referenced = {}

local function fail(message)
    failures = failures + 1
    print("FAIL " .. message)
end

local function want_paths(steps, hq)
    local paths = {}
    for i, step in ipairs(steps) do
        local family, size = step:match("^([%w_]+):?(%w*)$")
        if size ~= "" and hq then
            size = hq_size[size] or size
        end
        paths[i] = shader[size == "" and family or (family .. ":" .. size)]
            or error("test table has no entry for " .. step)
    end
    return paths
end

for id, steps in pairs(expected) do
    local profile = script.by_id[id]
    if not profile then
        fail("profile " .. id .. " is missing")
    else
        for _, hq in ipairs({ false, true }) do
            local got = script.expand(profile.steps, hq)
            local want = want_paths(steps, hq)
            local label = "profile " .. id .. (hq and " (hq)" or "")
            if #got ~= #want then
                fail(label .. ": " .. #got .. " shaders, expected " .. #want)
            else
                for i = 1, #want do
                    if got[i] ~= want[i] then
                        fail(label .. " shader " .. i .. ": " .. got[i] .. ", expected " .. want[i])
                    end
                end
            end
            for _, path in ipairs(got) do
                referenced[path] = true
            end
        end
    end
end

if #script.profiles ~= 6 then
    fail(#script.profiles .. " profiles, expected 6")
end

local want_keys = {
    "Ctrl+1/profile-a",
    "Ctrl+2/profile-b",
    "Ctrl+3/profile-c",
    "Ctrl+4/profile-a+a",
    "Ctrl+5/profile-b+b",
    "Ctrl+6/profile-c+a",
    "Ctrl+0/off",
    "Ctrl+a/menu",
}
if #calls.keys ~= #want_keys then
    fail(#calls.keys .. " key bindings, expected " .. #want_keys)
end
for i, key in ipairs(want_keys) do
    if calls.keys[i] ~= key then
        fail("key binding " .. i .. ": " .. tostring(calls.keys[i]) .. ", expected " .. key)
    end
end

-- Every shader the script can reference, so the Nix shader set can be compared
-- against it.
local list = {}
for path in pairs(referenced) do
    list[#list + 1] = path
end
table.sort(list)
print("SHADERS " .. table.concat(list, " "))

if failures > 0 then
    print(failures .. " failure(s)")
    os.exit(1)
end

print("ok")
