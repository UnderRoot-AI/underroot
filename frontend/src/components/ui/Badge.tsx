export default function Badge({ children, tone = "green" }: { children: React.ReactNode; tone?: "green"|"yellow"|"red"|"blue" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}
