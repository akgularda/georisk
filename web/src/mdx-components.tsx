import type { MDXComponents } from "mdx/types";

const components: MDXComponents = {
  h2: (props) => <h2 className="scroll-mt-28 font-semibold text-foreground" {...props} />,
  h3: (props) => <h3 className="scroll-mt-28 font-semibold text-foreground" {...props} />,
  p: (props) => <p className="text-base leading-8 text-[#2e343a]" {...props} />,
  a: (props) => <a className="text-accent underline decoration-accent/40 underline-offset-4" {...props} />,
  ul: (props) => <ul className="list-disc space-y-2 pl-5" {...props} />,
  ol: (props) => <ol className="list-decimal space-y-2 pl-5" {...props} />,
  blockquote: (props) => (
    <blockquote
      className="rounded-r-2xl border-l-2 border-accent/30 bg-accent-soft/50 px-5 py-4 text-sm text-[#454c54]"
      {...props}
    />
  ),
  hr: (props) => <hr className="my-8 border-border" {...props} />,
};

export function useMDXComponents(): MDXComponents {
  return components;
}
