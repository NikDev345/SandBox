/**
 * ============================================================
 * api.js — All network communication with the backend.
 *
 * Backend routes (see: app/routers/mock_api router, prefix "/api_mock"):
 *   POST   /api_mock/create   -> create a mock API
 *   GET    /api_mock/list     -> list mock APIs for current user
 *   GET    /api_mock/{id}     -> fetch a single mock API
 *   PUT    /api_mock/{id}     -> update a mock API
 *   DELETE /api_mock/{id}     -> delete a mock API
 *
 * All routes require an authenticated user (get_current_user),
 * so every request is sent with an "Authorization: Bearer <token>"
 * header. The token is configured from the Settings view.
 * ============================================================
 */

const API = (() => {
  const DEFAULT_BASE_URL = "http://127.0.0.1:8000";
  const STORAGE_BASE_URL = "mockgen:baseUrl";
  const STORAGE_TOKEN = "mockgen:authToken";

  function getBaseUrl() {
    return localStorage.getItem(STORAGE_BASE_URL) || DEFAULT_BASE_URL;
  }

  function setBaseUrl(url) {
    localStorage.setItem(STORAGE_BASE_URL, url.replace(/\/+$/, ""));
  }

  function getToken() {
    return localStorage.getItem(STORAGE_TOKEN) || "";
  }

  function setToken(token) {
    localStorage.setItem(STORAGE_TOKEN, token || "");
  }

  /**
   * Custom error carrying the HTTP status + parsed message,
   * so the UI layer can react appropriately (validation vs auth vs network).
   */
  class ApiError extends Error {
    constructor(message, status) {
      super(message);
      this.name = "ApiError";
      this.status = status;
    }
  }

  async function request(method, path, body) {
    const url = `${getBaseUrl()}${path}`;
    const headers = { "Content-Type": "application/json" };
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    let res;
    try {
      res = await fetch(url, {
        method,
        headers,
        body: body !== undefined ? JSON.stringify(body) : undefined,
      });
    } catch (networkErr) {
      throw new ApiError(
        "Could not reach the server. Check the API base URL in Settings and make sure the backend is running.",
        0
      );
    }

    let payload = null;
    const text = await res.text();
    if (text) {
      try {
        payload = JSON.parse(text);
      } catch (_) {
        payload = null;
      }
    }

    if (!res.ok) {
      const detail =
        (payload && (payload.detail || payload.message)) ||
        `Request failed with status ${res.status}`;
      const message =
        typeof detail === "string" ? detail : JSON.stringify(detail);
      throw new ApiError(message, res.status);
    }

    return payload;
  }

  /* ---------------------------------------------------------
     CRUD operations — payload shape matches MockAPIRequest
     exactly:
     {
       name, method, status_code,
       response_body, response_headers, response_delay_ms,
       authentication: { auth_type, bearer_token, api_key,
                          api_key_header, username, password }
     }
     --------------------------------------------------------- */

  function createMock(payload) {
    return request("POST", "/api_mock/create", payload);
  }

  function listMocks() {
    return request("GET", "/api_mock/list");
  }

  function getMock(id) {
    return request("GET", `/api_mock/${encodeURIComponent(id)}`);
  }

  function updateMock(id, payload) {
    return request("PUT", `/api_mock/${encodeURIComponent(id)}`, payload);
  }

  function deleteMock(id) {
    return request("DELETE", `/api_mock/${encodeURIComponent(id)}`);
  }

  return {
    DEFAULT_BASE_URL,
    getBaseUrl,
    setBaseUrl,
    getToken,
    setToken,
    ApiError,
    createMock,
    listMocks,
    getMock,
    updateMock,
    deleteMock,
  };
})();