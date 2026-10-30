import { describe as suite, expect, it } from "vitest";
import { describe } from "./reasons";

const r = (feature: string, value: number) => ({ feature, value, contribution: 0 });

suite("reason labels", () => {
  it("matches the wording used in the design", () => {
    expect(describe(r("has_https", 1))).toBe("Uses HTTPS");
    expect(describe(r("has_https", 0))).toBe("No HTTPS");
    expect(describe(r("subdomain_count", 0))).toBe("No subdomain");
    expect(describe(r("path_length", 6))).toBe("Has a path, 6 characters");
    expect(describe(r("path_length", 1))).toBe("Path is just a slash");
    expect(describe(r("has_file_extension", 0))).toBe("No file extension");
    expect(describe(r("url_entropy", 3.7))).toBe("Low randomness in the URL");
  });

  it("pluralises counts", () => {
    expect(describe(r("subdomain_count", 1))).toBe("1 subdomain");
    expect(describe(r("num_query_params", 2))).toBe("2 query parameters");
  });

  it("falls back to the feature name for unknown features", () => {
    expect(describe(r("brand_new_feature", 3))).toBe("brand new feature");
  });
});
