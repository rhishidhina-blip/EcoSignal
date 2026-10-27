/** Optional binding: this frontend does not use a hosted database. */
declare namespace Cloudflare {
  interface Env {
    DB?: D1Database;
  }
}
