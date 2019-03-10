 /*
 * Carla Plugin Host
 * Copyright (C) 2011-2019 Filipe Coelho <falktx@falktx.com>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of
 * the License, or any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * For a full copy of the GNU General Public License see the doc/GPL.txt file.
 */

#include "CarlaEngineOsc.hpp"

#ifdef HAVE_LIBLO

#include "CarlaEngineInternal.hpp"
#include "CarlaPlugin.hpp"
#include "CarlaMIDI.h"

#include <cctype>

CARLA_BACKEND_START_NAMESPACE

// -----------------------------------------------------------------------

int CarlaEngineOsc::handleMessage(const bool isTCP, const char* const path, const int argc, const lo_arg* const* const argv, const char* const types, const lo_message msg)
{
    CARLA_SAFE_ASSERT_RETURN(fName.isNotEmpty(), 1);
    CARLA_SAFE_ASSERT_RETURN(path != nullptr && path[0] != '\0', 1);
#ifdef DEBUG
    if (std::strstr(path, "/bridge_pong") == nullptr) {
        carla_debug("CarlaEngineOsc::handleMessage(%s, \"%s\", %i, %p, \"%s\", %p)", bool2str(isTCP), path, argc, argv, types, msg);
    }
#endif

    if (isTCP)
    {
        CARLA_SAFE_ASSERT_RETURN(fServerPathTCP.isNotEmpty(), 1);
        CARLA_SAFE_ASSERT_RETURN(fServerTCP != nullptr, 1);
    }
    else
    {
        CARLA_SAFE_ASSERT_RETURN(fServerPathUDP.isNotEmpty(), 1);
        CARLA_SAFE_ASSERT_RETURN(fServerUDP != nullptr, 1);
    }

    // Initial path check
    if (std::strcmp(path, "/register") == 0)
        return handleMsgRegister(isTCP, argc, argv, types);

    if (std::strcmp(path, "/unregister") == 0)
        return handleMsgUnregister(isTCP, argc, argv, types);

    if (std::strncmp(path, "/ctrl/", 6) == 0)
    {
        CARLA_SAFE_ASSERT_RETURN(isTCP, 1);
        return handleMsgControl(path + 6, argc, argv, types);
    }

    const std::size_t nameSize(fName.length());

    // Check if message is for this client
    if (std::strlen(path) <= nameSize || std::strncmp(path+1, fName, nameSize) != 0)
    {
        carla_stderr("CarlaEngineOsc::handleMessage() - message not for this client -> '%s' != '/%s/'",
                     path, fName.buffer());
        return 1;
    }

    // Get plugin id from path, "/carla/23/method" -> 23
    uint pluginId = 0;
    std::size_t offset;

    if (std::isdigit(path[nameSize+2]))
    {
        if (std::isdigit(path[nameSize+3]))
        {
            if (std::isdigit(path[nameSize+5]))
            {
                carla_stderr2("CarlaEngineOsc::handleMessage() - invalid plugin id, over 999? (value: \"%s\")", path+(nameSize+1));
                return 1;
            }
            else if (std::isdigit(path[nameSize+4]))
            {
                // 3 digits, /xyz/method
                offset    = 6;
                pluginId += uint(path[nameSize+2]-'0')*100;
                pluginId += uint(path[nameSize+3]-'0')*10;
                pluginId += uint(path[nameSize+4]-'0');
            }
            else
            {
                // 2 digits, /xy/method
                offset    = 5;
                pluginId += uint(path[nameSize+2]-'0')*10;
                pluginId += uint(path[nameSize+3]-'0');
            }
        }
        else
        {
            // single digit, /x/method
            offset    = 4;
            pluginId += uint(path[nameSize+2]-'0');
        }
    }
    else
    {
        carla_stderr("CarlaEngineOsc::handleMessage() - invalid message '%s'", path);
        return 1;
    }

    if (pluginId > fEngine->getCurrentPluginCount())
    {
        carla_stderr("CarlaEngineOsc::handleMessage() - failed to get plugin, wrong id '%i'", pluginId);
        return 0;
    }

    // Get plugin
    CarlaPlugin* const plugin(fEngine->getPluginUnchecked(pluginId));

    if (plugin == nullptr || plugin->getId() != pluginId)
    {
        carla_stderr("CarlaEngineOsc::handleMessage() - invalid plugin id '%i', probably has been removed (path: '%s')", pluginId, path);
        return 0;
    }

    // Get method from path, "/Carla/i/method" -> "method"
    char method[32+1];
    method[32] = '\0';
    std::strncpy(method, path + (nameSize + offset), 32);

    if (method[0] == '\0')
    {
        carla_stderr("CarlaEngineOsc::handleMessage(%s, \"%s\", ...) - received message without method", bool2str(isTCP), path);
        return 0;
    }

    // Internal methods
    if (std::strcmp(method, "set_option") == 0)
        return 0; //handleMsgSetOption(plugin, argc, argv, types); // TODO
    if (std::strcmp(method, "set_active") == 0)
        return handleMsgSetActive(plugin, argc, argv, types);
    if (std::strcmp(method, "set_drywet") == 0)
        return handleMsgSetDryWet(plugin, argc, argv, types);
    if (std::strcmp(method, "set_volume") == 0)
        return handleMsgSetVolume(plugin, argc, argv, types);
    if (std::strcmp(method, "set_balance_left") == 0)
        return handleMsgSetBalanceLeft(plugin, argc, argv, types);
    if (std::strcmp(method, "set_balance_right") == 0)
        return handleMsgSetBalanceRight(plugin, argc, argv, types);
    if (std::strcmp(method, "set_panning") == 0)
        return handleMsgSetPanning(plugin, argc, argv, types);
    if (std::strcmp(method, "set_ctrl_channel") == 0)
        return 0; //handleMsgSetControlChannel(plugin, argc, argv, types); // TODO
    if (std::strcmp(method, "set_parameter_value") == 0)
        return handleMsgSetParameterValue(plugin, argc, argv, types);
    if (std::strcmp(method, "set_parameter_midi_cc") == 0)
        return handleMsgSetParameterMidiCC(plugin, argc, argv, types);
    if (std::strcmp(method, "set_parameter_midi_channel") == 0)
        return handleMsgSetParameterMidiChannel(plugin, argc, argv, types);
    if (std::strcmp(method, "set_program") == 0)
        return handleMsgSetProgram(plugin, argc, argv, types);
    if (std::strcmp(method, "set_midi_program") == 0)
        return handleMsgSetMidiProgram(plugin, argc, argv, types);
    if (std::strcmp(method, "set_custom_data") == 0)
        return 0; //handleMsgSetCustomData(plugin, argc, argv, types); // TODO
    if (std::strcmp(method, "set_chunk") == 0)
        return 0; //handleMsgSetChunk(plugin, argc, argv, types); // TODO
    if (std::strcmp(method, "note_on") == 0)
        return handleMsgNoteOn(plugin, argc, argv, types);
    if (std::strcmp(method, "note_off") == 0)
        return handleMsgNoteOff(plugin, argc, argv, types);

    // Send all other methods to plugins, TODO
    plugin->handleOscMessage(method, argc, argv, types, msg);
    return 0;
}

// -----------------------------------------------------------------------

int CarlaEngineOsc::handleMsgRegister(const bool isTCP,
                                      const int argc, const lo_arg* const* const argv, const char* const types)
{
    carla_debug("CarlaEngineOsc::handleMsgRegister()");
    CARLA_ENGINE_OSC_CHECK_OSC_TYPES(1, "s");

    const char* const url = &argv[0]->s;
    const lo_address addr = lo_address_new_from_url(url);

    CarlaOscData& oscData(isTCP ? fControlDataTCP : fControlDataUDP);

    if (oscData.owner != nullptr)
    {
        carla_stderr("OSC backend already registered to %s", oscData.owner);

        char* const path = lo_url_get_path(url);

        char targetPath[std::strlen(path)+18];
        std::strcpy(targetPath, path);
        std::strcat(targetPath, "/exit-error");

        lo_send_from(addr, isTCP ? fServerTCP : fServerUDP, LO_TT_IMMEDIATE,
                     targetPath, "s", "OSC already registered to another client");

        free(path);
    }
    else
    {
        carla_stdout("OSC backend registered to %s", url);

        const char* const host  = lo_address_get_hostname(addr);
        const char* const port  = lo_address_get_port(addr);
        const lo_address target = lo_address_new_with_proto(isTCP ? LO_TCP : LO_UDP, host, port);

        oscData.owner  = carla_strdup_safe(url);
        oscData.path   = carla_strdup_free(lo_url_get_path(url));
        oscData.target = target;

        if (isTCP)
        {
            const EngineOptions& opts(fEngine->getOptions());

            fEngine->callback(false, true,
                              ENGINE_CALLBACK_ENGINE_STARTED, 0,
                              opts.processMode,
                              opts.transportMode,
                              static_cast<int>(fEngine->getBufferSize()),
                              static_cast<float>(fEngine->getSampleRate()),
                              fEngine->getCurrentDriverName());

            for (uint i=0, count=fEngine->getCurrentPluginCount(); i < count; ++i)
            {
                CarlaPlugin* const plugin(fEngine->getPluginUnchecked(i));
                CARLA_SAFE_ASSERT_CONTINUE(plugin != nullptr);

                fEngine->callback(false, true, ENGINE_CALLBACK_PLUGIN_ADDED, i, 0, 0, 0, 0.0f, plugin->getName());
            }

            fEngine->patchbayRefresh(false, true, fEngine->pData->graph.isUsingExternal());

#if 0
void CarlaPlugin::registerToOscClient() noexcept
{
    // Programs
    if (const uint32_t count = std::min<uint32_t>(pData->prog.count, 50U))
    {
        pData->engine->oscSend_control_set_program_count(pData->id, count);

        for (uint32_t i=0; i < count; ++i)
            pData->engine->oscSend_control_set_program_name(pData->id, i, pData->prog.names[i]);

//         pData->engine->oscSend_control_set_current_program(pData->id, pData->prog.current);
    }

    // MIDI Programs
    if (const uint32_t count = std::min<uint32_t>(pData->midiprog.count, 50U))
    {
        pData->engine->oscSend_control_set_midi_program_count(pData->id, count);

        for (uint32_t i=0; i < count; ++i)
        {
            const MidiProgramData& mpData(pData->midiprog.data[i]);

            pData->engine->oscSend_control_set_midi_program_data(pData->id, i, mpData.bank, mpData.program, mpData.name);
        }

//         pData->engine->oscSend_control_set_current_midi_program(pData->id, pData->midiprog.current);
    }
}
#endif

        }
    }

    lo_address_free(addr);
    return 0;
}

int CarlaEngineOsc::handleMsgUnregister(const bool isTCP,
                                        const int argc, const lo_arg* const* const argv, const char* const types)
{
    carla_debug("CarlaEngineOsc::handleMsgUnregister()");
    CARLA_ENGINE_OSC_CHECK_OSC_TYPES(1, "s");

    CarlaOscData& oscData(isTCP ? fControlDataTCP : fControlDataUDP);

    if (oscData.owner == nullptr)
    {
        carla_stderr("OSC backend is not registered yet, unregister failed");
        return 0;
    }

    const char* const url = &argv[0]->s;

    if (std::strcmp(oscData.owner, url) == 0)
    {
        carla_stdout("OSC client %s unregistered", url);
        oscData.clear();
        return 0;
    }

    carla_stderr("OSC backend unregister failed, current owner %s does not match requested %s", oscData.owner, url);
    return 0;
}

int CarlaEngineOsc::handleMsgControl(const char* const method,
                                     const int argc, const lo_arg* const* const argv, const char* const types)
{
    carla_debug("CarlaEngineOsc::handleMsgControl()");
    CARLA_SAFE_ASSERT_RETURN(method != nullptr && method[0] != '\0', 0);
    CARLA_SAFE_ASSERT_RETURN(types != nullptr, 0);

    if (fControlDataTCP.owner == nullptr)
    {
        carla_stderr("OSC backend is not registered yet, control failed");
        return 0;
    }

    /**/ if (std::strcmp(method, "clear_engine_xruns") == 0)
    {
        fEngine->clearXruns();
    }
    else if (std::strcmp(method, "cancel_engine_action") == 0)
    {
        fEngine->setActionCanceled(true);
    }
    else if (std::strcmp(method, "patchbay_connect") == 0)
    {
        CARLA_SAFE_ASSERT_INT_RETURN(argc == 4, argc, 0);
        CARLA_SAFE_ASSERT_RETURN(types[0] == 'i', 0);
        CARLA_SAFE_ASSERT_RETURN(types[1] == 'i', 0);
        CARLA_SAFE_ASSERT_RETURN(types[2] == 'i', 0);
        CARLA_SAFE_ASSERT_RETURN(types[3] == 'i', 0);

        const int32_t i0 = argv[0]->i;
        CARLA_SAFE_ASSERT_RETURN(i0 >= 0, 0);

        const int32_t i1 = argv[1]->i;
        CARLA_SAFE_ASSERT_RETURN(i1 >= 0, 0);

        const int32_t i2 = argv[2]->i;
        CARLA_SAFE_ASSERT_RETURN(i2 >= 0, 0);

        const int32_t i3 = argv[3]->i;
        CARLA_SAFE_ASSERT_RETURN(i3 >= 0, 0);

        fEngine->patchbayConnect(static_cast<uint32_t>(i0),
                                 static_cast<uint32_t>(i1),
                                 static_cast<uint32_t>(i2),
                                 static_cast<uint32_t>(i3));
    }
    else if (std::strcmp(method, "patchbay_disconnect") == 0)
    {
        CARLA_SAFE_ASSERT_INT_RETURN(argc == 1, argc, 0);
        CARLA_SAFE_ASSERT_RETURN(types[0] == 'i', 0);

        const int32_t i = argv[0]->i;
        CARLA_SAFE_ASSERT_RETURN(i >= 0, 0);

        fEngine->patchbayDisconnect(static_cast<uint32_t>(i));
    }
    else if (std::strcmp(method, "patchbay_refresh") == 0)
    {
        CARLA_SAFE_ASSERT_INT_RETURN(argc == 1, argc, 0);
        CARLA_SAFE_ASSERT_RETURN(types[0] == 'i', 0);

        const int32_t i = argv[0]->i;
        fEngine->patchbayRefresh(false, true, i != 0);
    }
    else if (std::strcmp(method, "transport_play") == 0)
    {
        CARLA_SAFE_ASSERT_INT_RETURN(argc == 0, argc, 0);
        fEngine->transportPlay();
    }
    else if (std::strcmp(method, "transport_pause") == 0)
    {
        CARLA_SAFE_ASSERT_INT_RETURN(argc == 0, argc, 0);
        fEngine->transportPause();
    }
    else if (std::strcmp(method, "transport_bpm") == 0)
    {
        CARLA_SAFE_ASSERT_INT_RETURN(argc == 1, argc, 0);
        CARLA_SAFE_ASSERT_RETURN(types[0] == 'f', 0);

        const double f = argv[0]->f;
        CARLA_SAFE_ASSERT_RETURN(f >= 0.0, 0);

        fEngine->transportBPM(f);
    }
    else if (std::strcmp(method, "transport_relocate") == 0)
    {
        CARLA_SAFE_ASSERT_INT_RETURN(argc == 1, argc, 0);
        uint64_t frame;

        /**/ if (types[0] == 'i')
        {
            const int32_t i = argv[0]->i;
            CARLA_SAFE_ASSERT_RETURN(i >= 0, 0);
            frame = static_cast<uint64_t>(i);
        }
        else if (types[0] == 'h')
        {
            const int64_t h = argv[0]->h;
            CARLA_SAFE_ASSERT_RETURN(h >= 0, 0);
            frame = static_cast<uint64_t>(h);
        }
        else
        {
            carla_stderr2("Wrong OSC type used for '%s'", method);
            return 0;
        }

        fEngine->transportRelocate(frame);
    }
    else if (std::strcmp(method, "add_plugin") == 0)
    {
        CARLA_SAFE_ASSERT_INT_RETURN(argc == 7, argc, 0);
        CARLA_SAFE_ASSERT_RETURN(types[0] == 'i', 0);
        CARLA_SAFE_ASSERT_RETURN(types[1] == 'i', 0);
        CARLA_SAFE_ASSERT_RETURN(types[2] == 's', 0);
        CARLA_SAFE_ASSERT_RETURN(types[3] == 's', 0);
        CARLA_SAFE_ASSERT_RETURN(types[4] == 's', 0);
        CARLA_SAFE_ASSERT_RETURN(types[6] == 'i', 0);

        const int32_t btype = argv[0]->i;
        CARLA_SAFE_ASSERT_RETURN(btype >= 0, 0);

        const int32_t ptype = argv[1]->i;
        CARLA_SAFE_ASSERT_RETURN(ptype >= 0, 0);

        const char* filename = &argv[2]->s;

        if (filename != nullptr && std::strcmp(filename, "(null)") == 0)
            filename = nullptr;

        const char* name = &argv[3]->s;

        if (name != nullptr && std::strcmp(name, "(null)") == 0)
            name = nullptr;

        const char* const label = &argv[4]->s;
        CARLA_SAFE_ASSERT_RETURN(label != nullptr && label[0] != '\0', 0);

        int64_t uniqueId;

        /**/ if (types[5] == 'i')
        {
            uniqueId = argv[5]->i;
        }
        else if (types[5] == 'h')
        {
            uniqueId = argv[5]->h;
        }
        else
        {
            carla_stderr2("Wrong OSC type used for '%s' uniqueId", method);
            return 0;
        }

        const int32_t options = argv[6]->i;
        CARLA_SAFE_ASSERT_RETURN(options >= 0, 0);

        fEngine->addPlugin(static_cast<BinaryType>(btype),
                           static_cast<PluginType>(ptype),
                           filename, name, label, uniqueId, nullptr, static_cast<uint32_t>(options));
    }
    else if (std::strcmp(method, "remove_plugin") == 0)
    {
        CARLA_SAFE_ASSERT_INT_RETURN(argc == 1, argc, 0);
        CARLA_SAFE_ASSERT_RETURN(types[0] == 'i', 0);

        const int32_t i = argv[0]->i;
        CARLA_SAFE_ASSERT_RETURN(i >= 0, 0);

        fEngine->removePlugin(static_cast<uint32_t>(i));
    }
    else if (std::strcmp(method, "remove_all_plugins") == 0)
    {
        CARLA_SAFE_ASSERT_INT_RETURN(argc == 0, argc, 0);

        fEngine->removeAllPlugins();
    }
    else if (std::strcmp(method, "rename_plugin") == 0)
    {
        CARLA_SAFE_ASSERT_INT_RETURN(argc == 2, argc, 0);
        CARLA_SAFE_ASSERT_RETURN(types[0] == 'i', 0);
        CARLA_SAFE_ASSERT_RETURN(types[1] == 's', 0);

        const int32_t i = argv[0]->i;
        CARLA_SAFE_ASSERT_RETURN(i >= 0, 0);

        const char* const s = &argv[0]->s;
        CARLA_SAFE_ASSERT_RETURN(s != nullptr && s[0] != '\0', 0);

        fEngine->renamePlugin(static_cast<uint32_t>(i), s);
    }
    else if (std::strcmp(method, "clone_plugin") == 0)
    {
        CARLA_SAFE_ASSERT_INT_RETURN(argc == 1, argc, 0);
        CARLA_SAFE_ASSERT_RETURN(types[0] == 'i', 0);

        const int32_t i = argv[0]->i;
        CARLA_SAFE_ASSERT_RETURN(i >= 0, 0);

        fEngine->clonePlugin(static_cast<uint32_t>(i));
    }
    else if (std::strcmp(method, "replace_plugin") == 0)
    {
        CARLA_SAFE_ASSERT_INT_RETURN(argc == 1, argc, 0);
        CARLA_SAFE_ASSERT_RETURN(types[0] == 'i', 0);

        const int32_t i = argv[0]->i;
        CARLA_SAFE_ASSERT_RETURN(i >= 0, 0);

        fEngine->replacePlugin(static_cast<uint32_t>(i));
    }
    else if (std::strcmp(method, "switch_plugins") == 0)
    {
        CARLA_SAFE_ASSERT_INT_RETURN(argc == 2, argc, 0);
        CARLA_SAFE_ASSERT_RETURN(types[0] == 'i', 0);
        CARLA_SAFE_ASSERT_RETURN(types[1] == 'i', 0);

        const int32_t i0 = argv[0]->i;
        CARLA_SAFE_ASSERT_RETURN(i0 >= 0, 0);

        const int32_t i1 = argv[0]->i;
        CARLA_SAFE_ASSERT_RETURN(i1 >= 0, 0);

        fEngine->switchPlugins(static_cast<uint32_t>(i0), static_cast<uint32_t>(i1));
    }
    else
    {
        carla_stderr2("Unhandled OSC control for '%s'", method);
    }

    return 0;
}

// -----------------------------------------------------------------------

int CarlaEngineOsc::handleMsgSetActive(CARLA_ENGINE_OSC_HANDLE_ARGS)
{
    carla_debug("CarlaEngineOsc::handleMsgSetActive()");
    CARLA_ENGINE_OSC_CHECK_OSC_TYPES(1, "i");

    const bool active = (argv[0]->i != 0);

    plugin->setActive(active, false, true);
    return 0;
}

int CarlaEngineOsc::handleMsgSetDryWet(CARLA_ENGINE_OSC_HANDLE_ARGS)
{
    carla_debug("CarlaEngineOsc::handleMsgSetDryWet()");
    CARLA_ENGINE_OSC_CHECK_OSC_TYPES(1, "f");

    const float value = argv[0]->f;

    plugin->setDryWet(value, false, true);
    return 0;
}

int CarlaEngineOsc::handleMsgSetVolume(CARLA_ENGINE_OSC_HANDLE_ARGS)
{
    carla_debug("CarlaEngineOsc::handleMsgSetVolume()");
    CARLA_ENGINE_OSC_CHECK_OSC_TYPES(1, "f");

    const float value = argv[0]->f;

    plugin->setVolume(value, false, true);
    return 0;
}

int CarlaEngineOsc::handleMsgSetBalanceLeft(CARLA_ENGINE_OSC_HANDLE_ARGS)
{
    carla_debug("CarlaEngineOsc::handleMsgSetBalanceLeft()");
    CARLA_ENGINE_OSC_CHECK_OSC_TYPES(1, "f");

    const float value = argv[0]->f;

    plugin->setBalanceLeft(value, false, true);
    return 0;
}

int CarlaEngineOsc::handleMsgSetBalanceRight(CARLA_ENGINE_OSC_HANDLE_ARGS)
{
    carla_debug("CarlaEngineOsc::handleMsgSetBalanceRight()");
    CARLA_ENGINE_OSC_CHECK_OSC_TYPES(1, "f");

    const float value = argv[0]->f;

    plugin->setBalanceRight(value, false, true);
    return 0;
}

int CarlaEngineOsc::handleMsgSetPanning(CARLA_ENGINE_OSC_HANDLE_ARGS)
{
    carla_debug("CarlaEngineOsc::handleMsgSetPanning()");
    CARLA_ENGINE_OSC_CHECK_OSC_TYPES(1, "f");

    const float value = argv[0]->f;

    plugin->setPanning(value, false, true);
    return 0;
}

int CarlaEngineOsc::handleMsgSetParameterValue(CARLA_ENGINE_OSC_HANDLE_ARGS)
{
    carla_debug("CarlaEngineOsc::handleMsgSetParameterValue()");
    CARLA_ENGINE_OSC_CHECK_OSC_TYPES(2, "if");

    const int32_t index = argv[0]->i;
    const float   value = argv[1]->f;

    CARLA_SAFE_ASSERT_RETURN(index >= 0, 0);

    plugin->setParameterValue(static_cast<uint32_t>(index), value, true, false, true);
    return 0;
}

int CarlaEngineOsc::handleMsgSetParameterMidiCC(CARLA_ENGINE_OSC_HANDLE_ARGS)
{
    carla_debug("CarlaEngineOsc::handleMsgSetParameterMidiCC()");
    CARLA_ENGINE_OSC_CHECK_OSC_TYPES(2, "ii");

    const int32_t index = argv[0]->i;
    const int32_t cc    = argv[1]->i;

    CARLA_SAFE_ASSERT_RETURN(index >= 0, 0);
    CARLA_SAFE_ASSERT_RETURN(cc >= -1 && cc < MAX_MIDI_CONTROL, 0);

    plugin->setParameterMidiCC(static_cast<uint32_t>(index), static_cast<int16_t>(cc), false, true);
    return 0;
}

int CarlaEngineOsc::handleMsgSetParameterMidiChannel(CARLA_ENGINE_OSC_HANDLE_ARGS)
{
    carla_debug("CarlaEngineOsc::handleMsgSetParameterMidiChannel()");
    CARLA_ENGINE_OSC_CHECK_OSC_TYPES(2, "ii");

    const int32_t index   = argv[0]->i;
    const int32_t channel = argv[1]->i;

    CARLA_SAFE_ASSERT_RETURN(index >= 0, 0);
    CARLA_SAFE_ASSERT_RETURN(channel >= 0 && channel < MAX_MIDI_CHANNELS, 0);

    plugin->setParameterMidiChannel(static_cast<uint32_t>(index), static_cast<uint8_t>(channel), false, true);
    return 0;
}

int CarlaEngineOsc::handleMsgSetProgram(CARLA_ENGINE_OSC_HANDLE_ARGS)
{
    carla_debug("CarlaEngineOsc::handleMsgSetProgram()");
    CARLA_ENGINE_OSC_CHECK_OSC_TYPES(1, "i");

    const int32_t index = argv[0]->i;

    CARLA_SAFE_ASSERT_RETURN(index >= -1, 0);

    plugin->setProgram(index, true, false, true);
    return 0;
}

int CarlaEngineOsc::handleMsgSetMidiProgram(CARLA_ENGINE_OSC_HANDLE_ARGS)
{
    carla_debug("CarlaEngineOsc::handleMsgSetMidiProgram()");
    CARLA_ENGINE_OSC_CHECK_OSC_TYPES(1, "i");

    const int32_t index = argv[0]->i;

    CARLA_SAFE_ASSERT_RETURN(index >= -1, 0);

    plugin->setMidiProgram(index, true, false, true);
    return 0;
}

int CarlaEngineOsc::handleMsgNoteOn(CARLA_ENGINE_OSC_HANDLE_ARGS)
{
    carla_debug("CarlaEngineOsc::handleMsgNoteOn()");
    CARLA_ENGINE_OSC_CHECK_OSC_TYPES(3, "iii");

    const int32_t channel = argv[0]->i;
    const int32_t note    = argv[1]->i;
    const int32_t velo    = argv[2]->i;

    CARLA_SAFE_ASSERT_RETURN(channel >= 0 && channel < MAX_MIDI_CHANNELS, 0);
    CARLA_SAFE_ASSERT_RETURN(note >= 0 && note < MAX_MIDI_NOTE, 0);
    CARLA_SAFE_ASSERT_RETURN(velo >= 0 && velo < MAX_MIDI_VALUE, 0);

    plugin->sendMidiSingleNote(static_cast<uint8_t>(channel), static_cast<uint8_t>(note), static_cast<uint8_t>(velo), true, false, true);
    return 0;
}

int CarlaEngineOsc::handleMsgNoteOff(CARLA_ENGINE_OSC_HANDLE_ARGS)
{
    carla_debug("CarlaEngineOsc::handleMsgNoteOff()");
    CARLA_ENGINE_OSC_CHECK_OSC_TYPES(2, "ii");

    const int32_t channel = argv[0]->i;
    const int32_t note    = argv[1]->i;

    CARLA_SAFE_ASSERT_RETURN(channel >= 0 && channel < MAX_MIDI_CHANNELS, 0);
    CARLA_SAFE_ASSERT_RETURN(note >= 0 && note < MAX_MIDI_NOTE, 0);

    plugin->sendMidiSingleNote(static_cast<uint8_t>(channel), static_cast<uint8_t>(note), 0, true, false, true);
    return 0;
}

// -----------------------------------------------------------------------

CARLA_BACKEND_END_NAMESPACE

#endif // HAVE_LIBLO
