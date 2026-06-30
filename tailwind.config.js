/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/ragtail/ragtail_admin/components/**/*.{px,py}",
    "./src/ragtail/ragtail_admin/classes.py",
    "./examples/demo/site_templates/**/*.px",
  ],
  safelist: [
    "ProseMirror",
    "richtext-toolbar",
    "richtext-toolbar-group",
    "richtext-toolbar-separator",
    "richtext-toolbar-btn",
    "richtext-toolbar-btn--text",
    "absolute",
    "-translate-x-1/2",
    "-translate-y-1/2",
  ],
  theme: {
    extend: {
      colors: {
        ragtail: {
          primary: "#2e1f5e",
          "primary-dark": "#261a4e",
          secondary: "#007d7e",
          "secondary-dark": "#006263",
          focus: "#00a885",
        },
      },
      minHeight: {
        "slim-header": "3.125rem",
      },
      width: {
        sidebar: "12.5rem",
        explorer: "20rem",
      },
      maxWidth: {
        login: "28rem",
        content: "60rem",
      },
    },
  },
  plugins: [],
};
