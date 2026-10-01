import type { ReactNode } from "react";
import { SourceTag } from "./SourceTag";
import type { SourceCategory } from "../../domain/corridor";

export function DataProvenanceNotice({
  category,
  children,
}: {
  category: SourceCategory;
  children: ReactNode;
}) {
  return (
    <div className="provenance" data-category={category}>
      <SourceTag category={category} />
      <p>{children}</p>
    </div>
  );
}
