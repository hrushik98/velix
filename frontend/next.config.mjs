// Where the FastAPI backend runs. Locally it is on port 8001; on Vercel it is
// set to the public tunnel URL, and Vercel proxies /api and /storage to it.
const BACKEND_URL = (process.env.BACKEND_URL || "http://127.0.0.1:8001").replace(/\/$/, "");

/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${BACKEND_URL}/api/:path*`,
      },
      {
        source: '/storage/:path*',
        destination: `${BACKEND_URL}/storage/:path*`,
      },
    ];
  },
};

export default nextConfig;
