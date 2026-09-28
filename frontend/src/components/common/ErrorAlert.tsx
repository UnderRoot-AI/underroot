export default function ErrorAlert({ message }: { message?: string }) {
  if (!message) return null;
  return <div className="alert alert-error">{message}</div>;
}
