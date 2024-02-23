import React, { useState, useEffect } from "react";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import utc from "dayjs/plugin/utc";
import InfiniteScroll from "react-infinite-scroll-component";
import PropTypes from "prop-types";
import Post from "./post"; // Import your Post component

dayjs.extend(relativeTime);
dayjs.extend(utc);

export default function Feed({url}) {
  const [posts, setPosts] = useState([]);
  const [nextUrl, setNextUrl] = useState("");
  const fetchData = () => {
    fetch(url, { credentials: "same-origin" })
      .then((response) => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then((data) => {
        const postList = [];
        setNextUrl(data.next);
        for (let i = 0; i < data.results.length; i+=1){
          postList.push(data.results[i])
        }
        setPosts([...posts, ...postList]);
      })
      .catch((error) => {console.error('There has been a problem with your fetch operation:', error)});
  };
  useEffect(() => {
    fetchData(url);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <InfiniteScroll
      dataLength={posts.length} // This is important field to render the next data
      next={() => {fetchData(nextUrl);}}
      hasMore={!!nextUrl}
    >
      {posts.map(post => (
        <Post key={`${post.postid}`} url={`/api/v1/posts/${post.postid}/`} />
      ))}
    </InfiniteScroll>
  );
}
Feed.propTypes = {
  url: PropTypes.string.isRequired,
};
