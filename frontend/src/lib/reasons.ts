import type { Reason } from "@/api/types";

const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;
const pct = (v: number) => `${Math.round(v * 100)}%`;

// Plain words for each feature at the value this URL actually has.
const LABELS: Record<string, (v: number) => string> = {
  url_length: (v) => `${v} characters long`,
  num_dots: (v) => plural(v, "dot"),
  num_digits: (v) => (v === 0 ? "No digits" : plural(v, "digit")),
  pct_digits: (v) => `${pct(v)} digits`,
  pct_alpha: (v) => `${pct(v)} letters`,
  num_special: (v) => plural(v, "special character"),
  pct_special: (v) => `${pct(v)} special characters`,
  unique_char_ratio: (v) => (v >= 0.5 ? "Few repeated characters" : "Many repeated characters"),
  num_percent_encoded: (v) => (v === 0 ? "No encoded characters" : plural(v, "encoded character")),
  url_entropy: (v) => (v < 4 ? "Low randomness in the URL" : "High randomness in the URL"),
  is_malformed: (v) => (v ? "The URL is malformed" : "The URL is well formed"),
  has_ip: (v) => (v ? "Host is an IP address" : "Host is a domain name"),
  has_https: (v) => (v ? "Uses HTTPS" : "No HTTPS"),
  host_length: (v) => `Host is ${v} characters`,
  path_length: (v) =>
    v === 0 ? "No path" : v === 1 ? "Path is just a slash" : `Has a path, ${v} characters`,
  num_query_params: (v) => (v === 0 ? "No query parameters" : plural(v, "query parameter")),
  has_hyphen_in_host: (v) => (v ? "Hyphen in the host" : "No hyphen in the host"),
  domain_length: (v) => `Domain name is ${v} characters`,
  tld_length: (v) => `TLD is ${v} characters`,
  subdomain_count: (v) => (v === 0 ? "No subdomain" : plural(v, "subdomain")),
  is_popular_tld: (v) => (v ? "Common TLD" : "Uncommon TLD"),
  has_file_extension: (v) => (v ? "Ends in a file extension" : "No file extension"),
  has_suspicious_extension: (v) => (v ? "Risky file type" : "No risky file type"),
};

export function describe(reason: Reason): string {
  return LABELS[reason.feature]?.(reason.value) ?? reason.feature.replaceAll("_", " ");
}
