/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
        './src/components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                'sos-yellow': {
                    50: '#FFFEF5',
                    100: '#FFF7D6',
                    200: '#FFECAD',
                    300: '#FFE184',
                    400: '#F4C430',
                    500: '#E5B120',
                    600: '#CC9E1C',
                    700: '#B38B18',
                    800: '#997814',
                    900: '#806410',
                },
            },
            animation: {
                'bounce-gentle': 'bounce-gentle 2s infinite',
            },
            keyframes: {
                'bounce-gentle': {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-5px)' },
                },
            },
        },
    },
    plugins: [],
};