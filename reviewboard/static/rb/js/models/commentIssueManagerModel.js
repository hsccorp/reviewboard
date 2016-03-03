/*
 * commentIssueManager takes care of setting the state of a particular
 * comment issue, and also takes care of notifying callbacks whenever
 * the state is successfully changed.
 */
RB.CommentIssueManager = Backbone.Model.extend({
    defaults: {
        reviewRequest: null
    },

    initialize: function() {
        this._comments = {};
    },

    /*
     * setCommentState - set the state of comment issue
     * @param reviewID the id for the review that the comment belongs to
     * @param commentID the id of the comment with the issue
     * @param commentType the type of comment, either "diff_comments",
     *                     "screenshot_comments", or "file_attachment_comments".
     * @param state the state to set the comment issue to - either
     *              "open", "resolved", or "dropped"
     */
    setCommentState: function(reviewID, commentID, commentType, state) {
        var comment = this._getComment(reviewID, commentID, commentType);
        this._requestState(comment, state);
    },

    /*
     * getCommentExtraData - get the extra data for a comment
     * @param reviewID the id for the review that the comment belongs to
     * @param commentID the id of the comment with the issue
     * @param commentType the type of comment, either "diff_comments",
     *                     "screenshot_comments", or "file_attachment_comments".
     */
    getCommentExtraData: function(reviewID, commentID, commentType) {
        var self = this;
        var comment = this._getComment(reviewID, commentID, commentType);
        comment.ready({
            ready: function() {
                self.trigger('extraDataAvailable', comment);
            }
        });
    },


    /*
     * setCommentExtraData - set the extra data for a comment
     * @param commentID the id of the comment with the issue
     */
    setCommentExtraData: function(reviewID, commentID, commentType, extraData) {
        var comment = this._getComment(reviewID, commentID, commentType);
        comment.ready({
            ready: function() {
                console.log("initiating saving extraData for commentId:" + commentID + " extraData:" + extraData);
                comment.set('extraData', _.clone(extraData));
                
                /* To get the serialized attributes of the extra_data */
                this.extraData = new RB.ExtraData();
                this.extraData.attributes = extraData;
                this.attr = this.extraData.toJSON();

                comment.save({
                    attrs: _.keys(this.attr),
                    success: function(comment, rsp) {
                        console.log("Comment extraData saved.");
                    },
                    failure: function(comment, rsp) {
                        console.log("Comment extraData NOT saved.");
                    }
                });

            }
        });
    },

    /*
     * A helper function to either generate the appropriate
     * comment object based on commentType, or to grab the
     * comment from a cache if it's been generated before.
     */
    _getComment: function(reviewID, commentID, commentType) {
        if (!this._comments[commentID]) {
            var comment = null,
                reviewRequest = this.get('reviewRequest');

            if (commentType === "diff_comments") {
                comment = reviewRequest
                    .createReview(reviewID)
                    .createDiffComment(commentID);
            } else if (commentType === "screenshot_comments") {
                comment = reviewRequest
                    .createReview(reviewID)
                    .createScreenshotComment(commentID);
            } else if (commentType === "file_attachment_comments") {
                comment = reviewRequest
                    .createReview(reviewID)
                    .createFileAttachmentComment(commentID);
            } else {
                console.log("getComment received unexpected comment type '%s'",
                            commentType);
            }

            this._comments[commentID] = comment;
        }

        return this._comments[commentID];
    },

    // Helper function to set the state of a comment
    _requestState: function(comment, state) {
        var self = this;

        comment.ready({
            ready: function() {
                var oldIssueStatus = comment.get('issueStatus');

                comment.set('issueStatus', state);
                comment.save({
                    attrs: ['issueStatus'],
                    success: function(comment, rsp) {
                        var rspComment = (rsp.diff_comment ||
                                          rsp.file_attachment_comment ||
                                          rsp.screenshot_comment);
                        self.trigger('issueStatusUpdated', comment,
                                     oldIssueStatus, rspComment.timestamp);
                    }
                });
            }
        });
    }
});
