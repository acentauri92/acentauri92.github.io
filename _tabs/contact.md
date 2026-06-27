---
layout: page
title: Contact
description: Get in touch with Dheeraj Reddy.
icon: fas fa-paper-plane
order: 4
---

<div class="contact-wrapper">
  <p class="contact-intro">Have a question, want to collaborate, or just want to say hi? Drop me a message and I'll get back to you.</p>

  <form id="contact-form" action="https://formspree.io/f/maqgovky" method="POST">
    <div class="contact-field">
      <label for="name">Name</label>
      <input type="text" id="name" name="name" placeholder="Your name" required>
    </div>
    <div class="contact-field">
      <label for="email">Email</label>
      <input type="email" id="email" name="email" placeholder="your@email.com" required>
    </div>
    <div class="contact-field">
      <label for="message">Message</label>
      <textarea id="message" name="message" rows="6" placeholder="What's on your mind?" required></textarea>
    </div>
    <button type="submit" class="contact-submit">Send Message</button>
    <p id="contact-error" class="contact-status error" style="display:none;">Something went wrong. Please try again.</p>
  </form>

  <div id="contact-success" class="contact-success" style="display:none;">
    <div class="contact-success-icon"><i class="fas fa-check-circle"></i></div>
    <h3 class="contact-success-heading">Message sent!</h3>
    <p class="contact-success-body">Thanks for reaching out. I'll get back to you soon.</p>
  </div>
</div>

<script>
(function () {
  var form = document.getElementById('contact-form');
  var error = document.getElementById('contact-error');
  var success = document.getElementById('contact-success');

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var btn = form.querySelector('.contact-submit');
    btn.textContent = 'Sending…';
    btn.disabled = true;
    error.style.display = 'none';

    fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { 'Accept': 'application/json' }
    }).then(function (response) {
      if (response.ok) {
        form.style.display = 'none';
        document.querySelector('.contact-intro').style.display = 'none';
        success.style.display = 'flex';
      } else {
        error.style.display = 'block';
        btn.textContent = 'Send Message';
        btn.disabled = false;
      }
    }).catch(function () {
      error.style.display = 'block';
      btn.textContent = 'Send Message';
      btn.disabled = false;
    });
  });
})();
</script>
