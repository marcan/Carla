/*
  ==============================================================================

   This file is part of the JUCE 6 technical preview.
   Copyright (c) 2020 - Raw Material Software Limited

   You may use this code under the terms of the GPL v3
   (see www.gnu.org/licenses).

   For this technical preview, this file is not subject to commercial licensing.

   JUCE IS PROVIDED "AS IS" WITHOUT ANY WARRANTY, AND ALL WARRANTIES, WHETHER
   EXPRESSED OR IMPLIED, INCLUDING MERCHANTABILITY AND FITNESS FOR PURPOSE, ARE
   DISCLAIMED.

  ==============================================================================
*/

namespace juce
{

//==============================================================================
/**
    Base class for listeners that want to know about changes to an AudioProcessor.

    Use AudioProcessor::addListener() to register your listener with an AudioProcessor.

    @see AudioProcessor

    @tags{Audio}
*/
class JUCE_API  AudioProcessorListener
{
public:
    //==============================================================================
    /** Destructor. */
    virtual ~AudioProcessorListener() = default;

    //==============================================================================
    /** Receives a callback when a parameter is changed.

        IMPORTANT NOTE: This will be called synchronously when a parameter changes, and
        many audio processors will change their parameter during their audio callback.
        This means that not only has your handler code got to be completely thread-safe,
        but it's also got to be VERY fast, and avoid blocking. If you need to handle
        this event on your message thread, use this callback to trigger an AsyncUpdater
        or ChangeBroadcaster which you can respond to on the message thread.
    */
    virtual void audioProcessorParameterChanged (AudioProcessor* processor,
                                                 int parameterIndex,
                                                 float newValue) = 0;

    /** Called to indicate that something else in the plugin has changed, like its
        program, number of parameters, etc.

        IMPORTANT NOTE: This will be called synchronously, and many audio processors will
        call it during their audio callback. This means that not only has your handler code
        got to be completely thread-safe, but it's also got to be VERY fast, and avoid
        blocking. If you need to handle this event on your message thread, use this callback
        to trigger an AsyncUpdater or ChangeBroadcaster which you can respond to later on the
        message thread.
    */
    virtual void audioProcessorChanged (AudioProcessor* processor) = 0;

    /** Indicates that a parameter change gesture has started.

        E.g. if the user is dragging a slider, this would be called when they first
        press the mouse button, and audioProcessorParameterChangeGestureEnd would be
        called when they release it.

        IMPORTANT NOTE: This will be called synchronously, and many audio processors will
        call it during their audio callback. This means that not only has your handler code
        got to be completely thread-safe, but it's also got to be VERY fast, and avoid
        blocking. If you need to handle this event on your message thread, use this callback
        to trigger an AsyncUpdater or ChangeBroadcaster which you can respond to later on the
        message thread.

        @see audioProcessorParameterChangeGestureEnd
    */
    virtual void audioProcessorParameterChangeGestureBegin (AudioProcessor* processor,
                                                            int parameterIndex);

    /** Indicates that a parameter change gesture has finished.

        E.g. if the user is dragging a slider, this would be called when they release
        the mouse button.

        IMPORTANT NOTE: This will be called synchronously, and many audio processors will
        call it during their audio callback. This means that not only has your handler code
        got to be completely thread-safe, but it's also got to be VERY fast, and avoid
        blocking. If you need to handle this event on your message thread, use this callback
        to trigger an AsyncUpdater or ChangeBroadcaster which you can respond to later on the
        message thread.

        @see audioProcessorParameterChangeGestureBegin
    */
    virtual void audioProcessorParameterChangeGestureEnd (AudioProcessor* processor,
                                                          int parameterIndex);
};

} // namespace juce
