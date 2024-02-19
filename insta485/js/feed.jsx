// src/components/Feed.jsx
import React, { useState, useEffect } from 'react';
import Post from './post'; // Import your Post component
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import utc from 'dayjs/plugin/utc';

dayjs.extend(relativeTime);
dayjs.extend(utc);

export default function Feed() {
  const [posts, setPosts] = useState([]);

  useEffect(() => {
    fetch('/api/v1/posts/') // Adjust this URL to match your API endpoint
        .then(response => {
            if (!response.ok) {
            throw new Error('Network response was not ok');
            }
            return response.json();
        })
      .then(data => {
        // Assuming the data returned is an array of posts
        setPosts(data.results); // Adjust based on the actual structure of your response
      })
      .catch(error => console.error('There has been a problem with your fetch operation:', error));
    }, []);
  

  return (
    <div>
      {posts.map(post => (
        <Post key={post.postid} url={`/api/v1/posts/${post.postid}/`} />
      ))}
    </div>
  );
}


