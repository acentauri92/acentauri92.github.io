---
layout: post
title: Linux Kernel and swear words
date: '2021-05-02 00:00:00'
categories: [software]
tags: [linux]     # TAG names should always be lowercase
image:
  path: /assets/images/linux-swear/linux_3_prev.png
  alt: image alternative text
comments: true
---

A while ago, while browsing through the Linux 5.13 source, I came across several swear words. Out of curiosity, I wanted to see if any more of these words existed. So, using the lovely little grep tool, I searched for some of the words and was amazed by how many of these were present. You can see a screenshot below to get an idea. 

![Local Image](/assets/images/linux-swear/linux_1.jpeg)

It turns out that there is a fun little webpage that does exactly this - Count the number of words matching your input. You can see the count for the word 'stupid' increases with every release. Are developers getting increasingly frustrated every year maybe? With the line count of the Linux source approaching 30 million, I'm not really surprised. 

![Local Image](/assets/images/linux-swear/linux_2.jpeg)

You can also checkout how different companies use their names in the source code. Looks like Google is the one that includes its nam ethe most. 

![Local Image](/assets/images/linux-swear/linux_3.png)

Go ahead and check out this <a href="https://www.vidarholen.net/contents/wordcount/" target="_blank">webpage</a>. You can type whatever word comes into your mind. 

 {% if page.comments %} <div id="disqus_thread"></div>
<script>
    /**
     *  RECOMMENDED CONFIGURATION VARIABLES: EDIT AND UNCOMMENT THE SECTION BELOW TO INSERT DYNAMIC VALUES FROM YOUR PLATFORM OR CMS.
     *  LEARN WHY DEFINING THESE VARIABLES IS IMPORTANT: https://disqus.com/admin/universalcode/#configuration-variables
     */
    /*
    var disqus_config = function () {
        this.page.url = PAGE_URL;  // Replace PAGE_URL with your page's canonical URL variable
        this.page.identifier = PAGE_IDENTIFIER; // Replace PAGE_IDENTIFIER with your page's unique identifier variable
    };
    */
    (function() {  // DON'T EDIT BELOW THIS LINE
        var d = document, s = d.createElement('script');
        
        s.src = 'https://https-acentauri92-github-io.disqus.com/embed.js';
        
        s.setAttribute('data-timestamp', +new Date());
        (d.head || d.body).appendChild(s);
    })();
</script>
<noscript>Please enable JavaScript to view the <a href="https://disqus.com/?ref_noscript" rel="nofollow">comments powered by Disqus.</a></noscript> {% endif %}