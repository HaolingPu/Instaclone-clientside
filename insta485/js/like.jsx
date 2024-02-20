// like.js
import React from 'react';
import PropTypes from 'prop-types';

export default function Likes({ numLikes, isLiked, handleLike }) {
    return (
      <p>
        <button onClick={handleLike} data-testid="like-unlike-button">
          {isLiked ? 'Unlike' : 'Like'}
        </button>
        <br/>
        <span>{numLikes} {numLikes === 1 ? 'like' : 'likes'}</span>
      </p>
    );
  }
  
  Likes.propTypes = {
    numLikes: PropTypes.number.isRequired,
    isLiked: PropTypes.bool.isRequired,
    handleLike: PropTypes.func.isRequired,
  };