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

class UIViewComponent::Pimpl  : public ComponentMovementWatcher
{
public:
    Pimpl (UIView* v, Component& comp)
        : ComponentMovementWatcher (&comp),
          view (v),
          owner (comp)
    {
        [view retain];

        if (owner.isShowing())
            componentPeerChanged();
    }

    ~Pimpl() override
    {
        [view removeFromSuperview];
        [view release];
    }

    void componentMovedOrResized (bool /*wasMoved*/, bool /*wasResized*/) override
    {
        auto* topComp = owner.getTopLevelComponent();

        if (topComp->getPeer() != nullptr)
        {
            auto pos = topComp->getLocalPoint (&owner, Point<int>());

            [view setFrame: CGRectMake ((float) pos.x, (float) pos.y,
                                        (float) owner.getWidth(), (float) owner.getHeight())];
        }
    }

    void componentPeerChanged() override
    {
        auto* peer = owner.getPeer();

        if (currentPeer != peer)
        {
            if ([view superview] != nil)
                [view removeFromSuperview]; // Must be careful not to call this unless it's required - e.g. some Apple AU views
                                            // override the call and use it as a sign that they're being deleted, which breaks everything..
            currentPeer = peer;

            if (peer != nullptr)
            {
                UIView* peerView = (UIView*) peer->getNativeHandle();
                [peerView addSubview: view];
                componentMovedOrResized (false, false);
            }
        }

        [view setHidden: ! owner.isShowing()];
     }

    void componentVisibilityChanged() override
    {
        componentPeerChanged();
    }

    Rectangle<int> getViewBounds() const
    {
        CGRect r = [view frame];
        return Rectangle<int> ((int) r.size.width, (int) r.size.height);
    }

    UIView* const view;

private:
    Component& owner;
    ComponentPeer* currentPeer = nullptr;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (Pimpl)
};

//==============================================================================
UIViewComponent::UIViewComponent() {}
UIViewComponent::~UIViewComponent() {}

void UIViewComponent::setView (void* view)
{
    if (view != getView())
    {
        pimpl.reset();

        if (view != nullptr)
            pimpl.reset (new Pimpl ((UIView*) view, *this));
    }
}

void* UIViewComponent::getView() const
{
    return pimpl == nullptr ? nullptr : pimpl->view;
}

void UIViewComponent::resizeToFitView()
{
    if (pimpl != nullptr)
        setBounds (pimpl->getViewBounds());
}

void UIViewComponent::paint (Graphics&) {}

} // namespace juce
