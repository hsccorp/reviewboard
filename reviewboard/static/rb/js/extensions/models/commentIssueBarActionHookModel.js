/*
 * Adds additional rendering or UI for a comment in the comment issue bar.
 *
 * This can be used to display additional UI and even additional fields on
 * the issue bar on the review page, which can reflect and potentially modify extra data
 * for a comment.
 *
 * A Backbone View type (not an instance) must be provided for the viewType
 * attribute. When rendering comments in the dialog, an instance of the
 * provided view will be created and passed the comment as the view's model.
 */
RB.CommentIssueBarActionHook = RB.ExtensionHook.extend({
    hookPoint: new RB.ExtensionHookPoint(),

    defaults: _.defaults({
        viewType: null
    }, RB.ExtensionHook.prototype.defaults),

    setUpHook: function() {
        console.assert(this.get('viewType'),
                       'CommentIssueBarActionHook instance does not have a ' +
                       '"viewType" attribute set.');
    }
});
