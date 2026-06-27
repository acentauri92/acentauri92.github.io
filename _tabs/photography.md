---
layout: page
title: Photography
description: A collection of photographs from my travels and everyday life.
icon: fas fa-camera
order: 2
---

<div class="photo-grid">
  {% for photo in site.data.photos %}
    <div
      class="photo-item"
      data-src="{{ '/assets/images/photos/' | append: photo.file | relative_url }}"
      data-desc="{{ photo.description }}"
    >
      <img
        src="{{ '/assets/images/photos/' | append: photo.file | relative_url }}"
        alt="{{ photo.description }}"
        loading="lazy"
      >
    </div>
  {% endfor %}
</div>

<script>
(function () {
  var photos = [];
  var current = 0;

  /* Build lightbox entirely in JS so it's never inside article */
  var lb = document.createElement('div');
  lb.id = 'photo-lightbox';
  lb.setAttribute('aria-hidden', 'true');
  lb.innerHTML = [
    '<button class="lb-close" aria-label="Close">&times;</button>',
    '<button class="lb-prev" aria-label="Previous">&#8249;</button>',
    '<div class="lb-content">',
    '  <img src="" alt="">',
    '  <p class="lb-caption"></p>',
    '</div>',
    '<button class="lb-next" aria-label="Next">&#8250;</button>'
  ].join('');
  document.body.appendChild(lb);

  var lbImg = lb.querySelector('img');
  var lbCaption = lb.querySelector('.lb-caption');

  /* Block any click on the lightbox image from bubbling or navigating */
  lbImg.addEventListener('click', function (e) {
    e.preventDefault();
    e.stopPropagation();
  }, true);

  document.querySelectorAll('.photo-grid .photo-item').forEach(function (item) {
    photos.push({ src: item.dataset.src, desc: item.dataset.desc || '' });
  });

  function show(index) {
    current = (index + photos.length) % photos.length;
    lbImg.src = photos[current].src;
    lbImg.alt = photos[current].desc;
    lbCaption.textContent = photos[current].desc;
    lbCaption.style.display = photos[current].desc ? '' : 'none';
    lb.classList.add('open');
    lb.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function close() {
    lb.classList.remove('open');
    lb.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    lbImg.src = '';
  }

  lb.querySelector('.lb-close').addEventListener('click', close);
  lb.querySelector('.lb-prev').addEventListener('click', function () { show(current - 1); });
  lb.querySelector('.lb-next').addEventListener('click', function () { show(current + 1); });
  lb.addEventListener('click', function (e) { if (e.target === lb) close(); });

  document.addEventListener('keydown', function (e) {
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowRight') show(current + 1);
    if (e.key === 'ArrowLeft') show(current - 1);
  });

  /* Capture phase intercepts click before Chirpy's popup handler */
  document.querySelector('.photo-grid').addEventListener('click', function (e) {
    var item = e.target.closest('.photo-item');
    if (!item) return;
    e.preventDefault();
    e.stopPropagation();
    var index = photos.findIndex(function (p) { return p.src === item.dataset.src; });
    if (index >= 0) show(index);
  }, true);
})();
</script>
