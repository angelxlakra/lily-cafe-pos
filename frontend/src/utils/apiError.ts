import type { AxiosError } from 'axios';

/** Plain-language reason a request failed, for staff-facing error messages. */
export function describeApiError(error: unknown): string {
  const axiosError = error as AxiosError<{ detail?: unknown }>;
  const response = axiosError?.response;
  if (!response && (axiosError?.code === 'ECONNABORTED' || axiosError?.code === 'ETIMEDOUT')) {
    return 'The server took too long to answer. It may still have gone through, so check before trying again.';
  }
  if (!response) return "Couldn't reach the server. Check the Wi-Fi and try again.";
  if (response.status === 401) return 'Your sign-in has expired. Sign in again, then try once more.';
  if (response.status === 403) return "This account isn't allowed to do that. Ask the owner to check your access.";
  const detail = response.data?.detail;
  return typeof detail === 'string' ? detail : 'The server had a problem. Try again in a moment.';
}
