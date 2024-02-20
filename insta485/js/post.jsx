import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import utc from "dayjs/plugin/utc";
import Likes from './like';
import Comment from "./comment";

dayjs.extend(relativeTime);
dayjs.extend(utc);

// The parameter of this function is an object with a string called url inside it.
// url is a prop for the Post component.
export default function Post({ url }) {
  /* Display image and post owner of a single post */
  const [post, setPost] = useState({
    comments: [],
    comments_url: "",
    created: "",
    imgUrl: "",
    lognameLikesThis: false,
    numLikes: 0,
    likeUrl: "",
    owner: "",
    ownerImgUrl: "",
    ownerShowUrl: "",
    postShowUrl: "",
    postid: -1,
    url: "",
  });


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

          setPost({
            comments: data.comments,
            comments_url: data.comments_url,
            created: dayjs(data.created).utc(true).fromNow(),
            imgUrl: data.imgUrl,
            lognameLikesThis: data.likes.lognameLikesThis,
            numLikes: data.likes.numLikes,
            likeUrl: data.likes.url,
            owner: data.owner,
            ownerImgUrl: data.ownerImgUrl,
            ownerShowUrl: data.ownerShowUrl,
            postShowUrl: data.postShowUrl,
            postid: data.postid,
            url: data.url,
          });
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

  function Postimg({ lognameLikesThis, img, handleLikeButton }) {
    const doubleClick = (event) => {
      if (lognameLikesThis === false) {
        handleLikeButton(event)
      }
  
    };
    return (< img src={img} onDoubleClick={doubleClick} alt="485post" className="image2"/>);
  }

  const handleLikeButton = () => {
    const targetUrl = post.lognameLikesThis ? post.likeUrl : `/api/v1/likes/?postid=${post.postid}`;
    // const newIsLiked = !post.lognameLikesThis;
    // const newNumLikes = post.numLikes + (newIsLiked ? 1 : -1);
    const method = post.lognameLikesThis ? "DELETE" : "POST";
    fetch(targetUrl,{method:method, credentials: "same-origin" })
        .then((response) => {
            if (!response.ok) throw Error(response.statusText);
            if (response.status === 204) {
                console.log("No content to parse");
                return null;
              } else {
                return response.json();
              }
        })
        .then((data) => {

            setPost(prevState => ({
                ...prevState,
                numLikes: prevState.numLikes + (prevState.lognameLikesThis ? -1 : 1),
                lognameLikesThis:!prevState.lognameLikesThis,   
                likeUrl: prevState.lognameLikesThis ? null : data.url,
              }));
        
        })
        .catch((error) => console.log(error));
  };

  

  return (
    <div className="post">
    <a href={post.ownerShowUrl}>
      <img src={post.ownerImgUrl} alt={post.owner} className="image1" />
      <p className="username"> {post.owner}</p>
    </a>
    <a href={post.postShowUrl}>
      <span className="time">{post.created}</span>
    </a>
    <br/>
    
      {/* <img src={post.imgUrl} alt="Post content" class="image2"/>
        <p>Check!!!</p>
        <span>{post.lognameLikesThis ? "1" : "0"} </span> */}
    {/* < img src={post.imgUrl} alt="Post content" class="image2" /> */}
      <Postimg lognameLikesThis={post.lognameLikesThis} img={post.imgUrl} handleLikeButton={handleLikeButton} />
    <br/>
    {post.url && (<Likes
        numLikes={post.numLikes}
        isLiked={post.lognameLikesThis}
        handleLike={handleLikeButton}
      />)
    }
    
    <br/>

    <Comment url={post.url} />
    
    
</div>
  );
}




Post.propTypes = {
  url: PropTypes.string.isRequired,
};
