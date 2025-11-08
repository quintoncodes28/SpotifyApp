/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    // Don’t fail the production build on ESLint errors
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;
