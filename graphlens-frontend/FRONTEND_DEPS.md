# Frontend dependency additions

After scaffolding with:

```bash
npx create-next-app@latest graphlens-frontend --typescript --app --src-dir --tailwind --eslint
```

install the extra packages GraphLens needs:

```bash
# Auth (Phase 8)
npm install next-auth

# HTTP + uploads + chat UI (Phase 7)
npm install axios react-dropzone
```

`--tailwind` already wires Tailwind CSS, so no manual setup is needed.
Copy `.env.local.example` to `.env.local` and fill in the values.
