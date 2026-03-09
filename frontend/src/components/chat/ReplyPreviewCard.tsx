interface ReplyPreviewCardProps {
  preview?: string;
}

export function ReplyPreviewCard({ preview }: ReplyPreviewCardProps) {
  return (
    <section className="card reply-preview-card">
      <h3>Reply Preview</h3>
      <p>{preview ?? "暂无回复预览"}</p>
    </section>
  );
}
