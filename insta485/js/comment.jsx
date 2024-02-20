// comment.js
import React, { useState, useEffect } from "react";
import PropTypes from 'prop-types';

export default function Comment({ url }) {
    /* Display image and post owner of a single post */
    const [comment, setComment] = useState([]);
    const [commentUrl, setcommentUrl] = useState("");
    const [newComment, setNewComment] = useState("");
  
  
    useEffect(() => {
      // Declare a boolean flag that we can use to cancel the API request.
      let ignoreStaleRequest = false;
  
      // Call REST API to get the post's information
      fetch(url, { credentials: "same-origin" })
        .then((response) => {
          if (!response.ok) throw Error(response.statusText);
          return response.json();
        })
        .then((data) => {
          if (!ignoreStaleRequest) {
            setComment(data.comments);
            setcommentUrl(data.comments_url);
          }
          
        })
        .catch((error) => console.log(error));
  
      return () => {
        ignoreStaleRequest = true;
      };
    }, [url]);

    const AddComment = (event) => {
            event.preventDefault();
            const trimmedComment = newComment.trim();
            if (trimmedComment) {
                console.log(commentUrl, "sdsds");
                fetch(commentUrl, {
                method: 'POST',
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ text: trimmedComment }),
                credentials: "same-origin", // Important for including cookies with the request if using session-based authentication
                })
                .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
                })
                .then(addedComment => {
                // Assuming the backend returns the added comment in a format compatible with your comments state
                setComment(prevComments => [...prevComments, {...addedComment, lognameOwnsThis: true}]);
                setNewComment(""); // Clear input field after successful submission
                })
                .catch(error => console.error('Error adding comment:', error));
            }
    };

 

    const DeleteComment = (commentid) => {
    // Call API to delete the comment
    // Then optimistically update the comments list or refetch comments
        fetch(`/api/v1/comments/${commentid}`, {method : "DELETE", credentials: "same-origin",})
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                if (response.status === 204) {
                    console.log("No content to parse");
                    return null;
                  } else {
                    return response.json();
                  }
            })
            .then(() => {
                setComment(comment.filter(comment => comment.commentid !== commentid));
            })
            .catch((error) => {
                console.error("Error deleting comment:", error);
              });

    };



    return (
        <>
        {comment.length !==0 && comment.map((c)=> (
            <p key={c.commentid} className="comment">
            <a href={c.ownerShowUrl}>{c.owner}</a>: 
            <span data-testid="comment-text">{c.text}</span>
            {c.lognameOwnsThis && (<button
            onClick={() => DeleteComment(c.commentid)}
            data-testid="delete-comment-button"
            >
            Delete
            </button>)}
            </p>

        ))}
        <br/>
        {commentUrl &&(<form data-testid="comment-form" onSubmit={AddComment}>
                <input
                type="text"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Add a comment..."
                />
        </form>)}
        </>
    );
    
}


    
Comment.propTypes = {
    url: PropTypes.string.isRequired,
  };