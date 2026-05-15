import Link from "next/link";

const links = [
  { href: "/", label: "Nova analise" },
  { href: "/agent", label: "Agente" },
  { href: "/catalog", label: "Catalogo" },
  { href: "/history", label: "Historico" },
  { href: "/insights", label: "Insights" },
];

export function AppNav() {
  return (
    <header className="border-b border-ink/10 bg-white/85 backdrop-blur">
      <nav className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <Link href="/" className="text-lg font-semibold text-ink">
          SkinMatch AI
        </Link>
        <div className="flex flex-wrap gap-2">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-md px-3 py-2 text-sm font-medium text-moss transition hover:bg-linen hover:text-ink"
            >
              {link.label}
            </Link>
          ))}
        </div>
      </nav>
    </header>
  );
}
