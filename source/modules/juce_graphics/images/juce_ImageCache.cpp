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

struct ImageCache::Pimpl     : private Timer,
                               private DeletedAtShutdown
{
    Pimpl() {}
    ~Pimpl() override { clearSingletonInstance(); }

    JUCE_DECLARE_SINGLETON_SINGLETHREADED_MINIMAL (ImageCache::Pimpl)

    Image getFromHashCode (const int64 hashCode) noexcept
    {
        const ScopedLock sl (lock);

        for (auto& item : images)
        {
            if (item.hashCode == hashCode)
            {
                item.lastUseTime = Time::getApproximateMillisecondCounter();
                return item.image;
            }
        }

        return {};
     }

    void addImageToCache (const Image& image, const int64 hashCode)
    {
        if (image.isValid())
        {
            if (! isTimerRunning())
                startTimer (2000);

            const ScopedLock sl (lock);
            images.add ({ image, hashCode, Time::getApproximateMillisecondCounter() });
        }
    }

    void timerCallback() override
    {
        auto now = Time::getApproximateMillisecondCounter();

        const ScopedLock sl (lock);

        for (int i = images.size(); --i >= 0;)
        {
            auto& item = images.getReference(i);

            if (item.image.getReferenceCount() <= 1)
            {
                if (now > item.lastUseTime + cacheTimeout || now < item.lastUseTime - 1000)
                    images.remove (i);
            }
            else
            {
                item.lastUseTime = now; // multiply-referenced, so this image is still in use.
            }
        }

        if (images.isEmpty())
            stopTimer();
    }

    void releaseUnusedImages()
    {
        const ScopedLock sl (lock);

        for (int i = images.size(); --i >= 0;)
            if (images.getReference(i).image.getReferenceCount() <= 1)
                images.remove (i);
    }

    struct Item
    {
        Image image;
        int64 hashCode;
        uint32 lastUseTime;
    };

    Array<Item> images;
    CriticalSection lock;
    unsigned int cacheTimeout = 5000;

    JUCE_DECLARE_NON_COPYABLE (Pimpl)
};

JUCE_IMPLEMENT_SINGLETON (ImageCache::Pimpl)


//==============================================================================
Image ImageCache::getFromHashCode (const int64 hashCode)
{
    if (Pimpl::getInstanceWithoutCreating() != nullptr)
        return Pimpl::getInstanceWithoutCreating()->getFromHashCode (hashCode);

    return {};
}

void ImageCache::addImageToCache (const Image& image, const int64 hashCode)
{
    Pimpl::getInstance()->addImageToCache (image, hashCode);
}

Image ImageCache::getFromFile (const File& file)
{
    auto hashCode = file.hashCode64();
    auto image = getFromHashCode (hashCode);

    if (image.isNull())
    {
        image = ImageFileFormat::loadFrom (file);
        addImageToCache (image, hashCode);
    }

    return image;
}

Image ImageCache::getFromMemory (const void* imageData, const int dataSize)
{
    auto hashCode = (int64) (pointer_sized_int) imageData;
    auto image = getFromHashCode (hashCode);

    if (image.isNull())
    {
        image = ImageFileFormat::loadFrom (imageData, (size_t) dataSize);
        addImageToCache (image, hashCode);
    }

    return image;
}

void ImageCache::setCacheTimeout (const int millisecs)
{
    jassert (millisecs >= 0);
    Pimpl::getInstance()->cacheTimeout = (unsigned int) millisecs;
}

void ImageCache::releaseUnusedImages()
{
    Pimpl::getInstance()->releaseUnusedImages();
}

} // namespace juce
