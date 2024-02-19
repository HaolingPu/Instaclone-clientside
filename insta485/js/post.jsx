import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import utc from "dayjs/plugin/utc";

dayjs.extend(relativeTime);
dayjs.extend(utc);


// The parameter of this function is an object with a string called url inside it.
// url is a prop for the Post component.
export default function Post({ url }) {
  /* Display image and post owner of a single post */

  const [imgUrl, setImgUrl] = useState("");
  const [owner, setOwner] = useState("");
  const [createdTime, setCreatedTime] = useState("");
  const [likes, setLikes] = useState({ lognameLikesThis: false, numLikes: 0 });
  const [comments, setComments] = useState([]);
  const [ownerImgUrl, setOwnerImgUrl] = useState("");


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
        // If ignoreStaleRequest was set to true, we want to ignore the results of the
        // the request. Otherwise, update the state to trigger a new render.
        if (!ignoreStaleRequest) {
          setImgUrl(data.imgUrl);
          setOwner(data.owner);
    
          setOwnerImgUrl(data.ownerImgUrl);
          setCreatedTime(dayjs.utc(data.created).local().fromNow());
          setLikes(data.likes);
          setComments(data.comments);
        }
      })
      .catch((error) => console.log(error));

    return () => {
      // This is a cleanup function that runs whenever the Post component
      // unmounts or re-renders. If a Post is about to unmount or re-render, we
      // should avoid updating state.
      ignoreStaleRequest = true;
    };
  }, [url]);

  // Render post image and post owner
  return (
    // <div className="post">
    //   <img src={imgUrl} alt="post_image" />
    //   <p>{owner}</p>
    //   <p>Posted {createdTime}</p>
    // </div>
    <div class="post">
    <a href={`/users/${owner}/`}>
      <img src={ownerImgUrl} alt="{{ post.owner }}" className="image1" />
      <p className="username"> {owner}</p>
    </a>
    <a href={url}>
      <span class="time">{createdTime}</span>
    </a>
    <br/>
    <a href={`/users/${owner}/`}>
      <img src={imgUrl} alt="Post content" class="image2"/>
    </a>
    <br/>
    <button>{likes.lognameLikesThis ? 'Unlike' : 'Like'}</button>
    <p>{likes.numLikes} {likes.numLikes === 1 ? 'like' : 'likes'}</p>
    
    <br/>
    {comments.map(comment => (
          <p key={comment.commentid} className="comment">
            <a href={comment.ownerShowUrl}>{comment.owner}</a>: {comment.text}
          </p>
          
        ))}
</div>
  );
}




Post.propTypes = {
  url: PropTypes.string.isRequired,
};
