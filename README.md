# jk4y.com

## Description
Personal website serving as a digital resume, blog/newsletter, and landing page for an upcoming MVP application. Built with Hugo and deployed to GitHub Pages.

## WordPress Migration

This site is being migrated from WordPress. The initial export is processed using `wordpress-export-to-markdown` to convert the WordPress XML into Hugo-compatible Markdown and download associated images.

### Migration Steps

1. **Run the Conversion Tool**:
   Ensure you have Node.js installed. Open your terminal and run the following command:

   ```bash
   npx wordpress-export-to-markdown
   ```

2. **Follow the Interactive Prompts**:
   - **Path to XML file**: `c:\Users\joshh\Projects\github.com\thomasf\exitwp\wordpress-xml\jhaxllc.WordPress.2026-02-25.xml`
   - **Path to output folder**: `./content/posts` (or your preferred Hugo content directory)
   - **Save images attached to posts?**: Yes
   - **Save images scraped from post body content?**: Yes
   - **Create year/month folders?**: (Your preference, Hugo handles flat or nested structures well)

3. **Fine-tune for Hugo**:
   While this tool outputs excellent Markdown, you may still need to adjust specific Hugo shortcodes or custom frontmatter. Use the `wordpress-migrator` agent (located in `agents/wordpress-migrator.md`) to help with any final cleanup.

## Agents

This repository includes several AI agent prompts in the `agents/` directory to assist with site management:
- **Content Writer / Editor**: Helps draft and format blog posts and pages.
- **SEO Optimizer**: Suggests improvements for frontmatter and content structure.
- **Deployment & CI/CD Manager**: Assists with GitHub Actions and GitHub Pages deployment.
- **WordPress Migrator**: Helps convert Jekyll-formatted Markdown from `exitwp` into Hugo format.
