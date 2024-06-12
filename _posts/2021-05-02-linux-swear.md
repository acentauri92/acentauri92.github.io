---
layout: post
title: Linux Kernel and swear words
date: '2021-05-02 00:00:00'
categories: [software]
tags: [linux]     # TAG names should always be lowercase
---

A while ago, while browsing through the Linux 5.13 source, I came across several swear words. Out of curiosity, I wanted to see if any more of these words existed. So, using the lovely little grep tool, I searched for some of the words and was amazed by how many of these were present. You can see a screenshot below to get an idea. 

![Local Image](/assets/images/linux-swear/linux_1.jpeg)

It turns out that there is a fun little webpage that does exactly this - Count the number of words matching your input. You can see the count for the word 'stupid' increases with every release. Are developers getting increasingly frustrated every year maybe? With the line count of the Linux source approaching 30 million, I'm not really surprised. 

![Local Image](/assets/images/linux-swear/linux_2.jpeg)

You can also checkout how different companies use their names in the source code. Looks like Google is the one that includes its nam ethe most. 

![Local Image](/assets/images/linux-swear/linux_3.png)

Go ahead and check out this <a href="https://www.vidarholen.net/contents/wordcount/" target="_blank">webpage</a>. You can type whatever word comes into your mind. 