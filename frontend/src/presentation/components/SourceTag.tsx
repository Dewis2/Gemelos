import { SOURCE_CATEGORY_LABELS, type SourceCategory } from "../../domain/corridor";

export function SourceTag({ category }: { category: SourceCategory }) {
  return <span className="source-tag" data-category={category}>{SOURCE_CATEGORY_LABELS[category]}</span>;
}
