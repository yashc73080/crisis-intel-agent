/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_GOOGLE_MAPS_API_KEY: process.env.GOOGLE_MAPS_API_KEY,
    NEXT_PUBLIC_API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
  },
};

export default nextConfig;
