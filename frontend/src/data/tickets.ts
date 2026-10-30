export type Ticket = {
  label: string;
  hint: string;
  url: string;
  /** Ground truth we know from outside the model, so a wrong verdict can be called out. */
  knownPhishing?: boolean;
  /** What Pawny says about this exact link once it is appraised. */
  remark?: string;
};

export const TICKETS: Ticket[] = [
  {
    label: "github.com/login",
    hint: "an everyday login page",
    url: "https://github.com/login",
  },
  {
    label: "paypal-verify.xyz/login",
    hint: "smells like bait",
    url: "http://paypal-verify.xyz/login",
    remark: "Plain HTTP, a brand name glued to a cheap TLD and a login path. Classic bait.",
  },
  {
    label: "mu.qmmafe.com",
    hint: "the one that fools Pawny",
    url: "https://mu.qmmafe.com/",
    knownPhishing: true,
  },
];
