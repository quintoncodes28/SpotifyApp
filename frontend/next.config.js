/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    // ✅ This tells Vercel to skip ESLint checks during builds
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;
