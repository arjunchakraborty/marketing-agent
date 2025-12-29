# Sample Email Templates

This directory contains sample HTML email templates that you can use for customer campaigns.

## Files

1. **sample_email.html** - Full-featured email template with:
   - Header with gradient background
   - Hero image
   - Discount badge
   - CTA button
   - Product grid (4 products)
   - Urgency indicator
   - Social proof
   - Footer with links

2. **email_template_simple.html** - Simplified version with:
   - Header
   - Banner image
   - Content section
   - Single CTA button
   - Footer

## How to Use

### Option 1: Use with Email Service (Klaviyo, Mailchimp, etc.)

1. Copy the HTML content from either template
2. Paste into your email service's HTML editor
3. Replace placeholder URLs and text with your actual content
4. Replace image URLs with your own images or hosted images
5. Send test email to yourself first

### Option 2: Save as HTML and Open in Browser

1. Open the HTML file in a web browser
2. Take a screenshot for preview
3. Use the HTML code in your email service

### Option 3: Use for Campaign Image Analysis

1. Take a screenshot of the email template
2. Save as PNG/JPG
3. Upload to `/campaigns/images` for analysis
4. The system will analyze visual elements, colors, CTAs, etc.

## Customization

### Replace Image URLs

The templates use Unsplash placeholder images. Replace with your own:

```html
<!-- Replace this -->
<img src="https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=600&h=300&fit=crop" />

<!-- With your image -->
<img src="https://yourdomain.com/images/summer-sale-banner.jpg" />
```

### Update Links

Replace all `https://example.com` links with your actual URLs:

```html
<a href="https://yourstore.com/shop">Shop Now →</a>
```

### Change Colors

Update the color scheme in the `<style>` section:

```css
.header {
    background-color: #your-color;
}
.cta-button {
    background-color: #your-cta-color;
}
```

### Add Your Branding

- Update "Your Brand Name" in the footer
- Add your logo to the header
- Update contact information

## Best Practices

1. **Test on Multiple Devices** - Emails look different on mobile vs desktop
2. **Use Web-Safe Fonts** - Arial, Helvetica, Times New Roman work best
3. **Optimize Images** - Keep image file sizes small for faster loading
4. **Include Alt Text** - Always add alt attributes to images
5. **Test Links** - Make sure all links work before sending
6. **Check Spam Score** - Use tools like Mail-Tester before sending

## For Campaign Analysis

When you upload these email templates as images:

1. The system will detect:
   - CTA buttons (red "Shop Now" button)
   - Discount badges (50% OFF)
   - Product images
   - Color schemes (purple gradient, red CTA)
   - Urgency indicators (countdown timer text)
   - Social proof (customer testimonial)

2. These elements will be correlated with campaign performance metrics to identify what works best.

## Next Steps

1. Customize the template with your branding
2. Upload to your email service
3. Send to a test list
4. Capture the email as an image
5. Upload the image to `/campaigns/images` for analysis
6. Use insights to improve future campaigns

