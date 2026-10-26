// Docs site for agentwaste, deployed to GitHub Pages by .github/workflows/docs.yml.
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import sidebar from './sidebar.json' with { type: 'json' };

export default defineConfig({
  site: 'https://nikghodki.github.io',
  base: '/agentwaste',
  integrations: [
    starlight({
      title: 'agentwaste',
      description: 'Find where your AI coding agent wastes tokens, and how to stop it.',
      social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/nikghodki/agentwaste' }],
      editLink: { baseUrl: 'https://github.com/nikghodki/agentwaste/edit/main/docs/' },
      customCss: ['./src/styles/custom.css'],
      sidebar,
    }),
  ],
});
