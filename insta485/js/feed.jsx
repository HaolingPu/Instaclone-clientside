import React, { useState, useEffect } from 'react';
import Post from './post'; // Import your Post component
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import utc from 'dayjs/plugin/utc';
import InfiniteScroll from 'react-infinite-scroll-component';

dayjs.extend(relativeTime);
dayjs.extend(utc);

export default function Feed() {
  const [posts, setPosts] = useState([]);
  const [nextUrl, setNextUrl] = useState("");

  const fetchData = () => {
    fetch('/api/v1/posts/', { credentials: "same-origin" })
      .then((response) => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then((data) => {
        const postList = [];
        for (let i = 0; i < data.results.length; i++){
          postList.push(data.results[i])
        }
        setPosts([...posts, ...postList]);
        setNextUrl(data.next);
      })
      .catch(error => console.error('There has been a problem with your fetch operation:', error));
  };

  useEffect(() => {
    fetchData();
  }, []);
  
  return (
    <InfiniteScroll
      dataLength={posts.length} // This is important field to render the next data
      next={() => {
        fetchData();
      }}
      hasMore={!!nextUrl}
    >
      {posts.map(post => (
        <Post key={post.postid} url={`/api/v1/posts/${post.postid}/`} />
      ))}
    </InfiniteScroll>
  );
}