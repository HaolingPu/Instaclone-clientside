// comment.js
import React from 'react';
import PropTypes from 'prop-types';



const handleAddComment = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        const trimmedComment = newComment.trim();
        if (trimmedComment) {
            // Replace '3' with the actual post ID variable if you have it dynamically
            const postId = postid; // Example static post ID, replace with dynamic data if necessary
            const commentPayload = { text: trimmedComment };
      
            fetch(`/api/v1/comments/?postid=${postId}`, {
              method: 'POST',
              
              body: JSON.stringify(commentPayload),
              credentials: 'include', // Important for including cookies with the request if using session-based authentication
            })
            .then(response => {
              if (!response.ok) throw new Error('Network response was not ok');
              return response.json();
            })
            .then(addedComment => {
              // Assuming the backend returns the added comment in a format compatible with your comments state
              setComments(prevComments => [...prevComments, {addedComment, lognameOwnsThis: true}]);
              setNewComment(""); // Clear input field after successful submission
            })
            .catch(error => console.error('Error adding comment:', error));
          }
    }
  };

  const handleCommentChange = (event) => {
    setNewComment(event.target.value);
  };

    const handleDeleteComment = (commentid) => {
    // Call API to delete the comment
    // Then optimistically update the comments list or refetch comments
    setComments(comments.filter(comment => comment.commentid !== commentid));
    };

export default function comment (){

}
{comment.lognameOwnsThis && (
    <button
        onClick={() => handleDeleteComment(comment.commentid)}
        data-testid="delete-comment-button"
    >
        Delete
    </button>
    )}

<form data-testid="comment-form" onSubmit={handleAddComment}>
        <input
          type="text"
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder="Add a comment..."
        />
      </form>