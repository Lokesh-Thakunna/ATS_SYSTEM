import api from '../services/api';

const blobUrlCache = new Map();
const accessMetaCache = new Map();

const toAccessMetaUrl = (resumeUrl) => {
  if (!resumeUrl) return '';
  return resumeUrl.replace(/\/file\/?$/, '/access/');
};

const revokeCachedBlob = (resumeUrl) => {
  const cached = blobUrlCache.get(resumeUrl);
  if (cached) {
    URL.revokeObjectURL(cached);
    blobUrlCache.delete(resumeUrl);
  }
};

export const getResumeAccessMeta = async (resumeUrl, { forceRefresh = false } = {}) => {
  if (!resumeUrl) {
    throw new Error('Resume URL is missing');
  }

  if (!forceRefresh && accessMetaCache.has(resumeUrl)) {
    return accessMetaCache.get(resumeUrl);
  }

  const accessMetaUrl = toAccessMetaUrl(resumeUrl);
  if (!accessMetaUrl || accessMetaUrl === resumeUrl) {
    const fallback = { url: resumeUrl, requires_auth: true };
    accessMetaCache.set(resumeUrl, fallback);
    return fallback;
  }

  const response = await api.get(accessMetaUrl);
  const meta = response.data || {};
  accessMetaCache.set(resumeUrl, meta);
  return meta;
};

export const getAuthenticatedResumeBlobUrl = async (resumeUrl, { forceRefresh = false } = {}) => {
  if (!resumeUrl) {
    throw new Error('Resume URL is missing');
  }

  const accessMeta = await getResumeAccessMeta(resumeUrl, { forceRefresh });
  if (accessMeta?.url && accessMeta.requires_auth === false) {
    return accessMeta.url;
  }

  if (!forceRefresh && blobUrlCache.has(resumeUrl)) {
    return blobUrlCache.get(resumeUrl);
  }

  if (forceRefresh) {
    revokeCachedBlob(resumeUrl);
  }

  const response = await api.get(resumeUrl, {
    responseType: 'blob',
  });

  const blobUrl = URL.createObjectURL(response.data);
  blobUrlCache.set(resumeUrl, blobUrl);
  return blobUrl;
};

export const openAuthenticatedResume = async (resumeUrl) => {
  const popup = window.open('', '_blank', 'noopener,noreferrer');

  try {
    if (popup) {
      popup.document.write('<title>Opening resume...</title><p style="font-family: sans-serif; padding: 16px;">Loading resume...</p>');
      popup.document.close();
    }

    const targetUrl = await getAuthenticatedResumeBlobUrl(resumeUrl, { forceRefresh: true });

    if (popup) {
      popup.location.replace(targetUrl);
    } else {
      window.open(targetUrl, '_blank', 'noopener,noreferrer');
    }

    return targetUrl;
  } catch (error) {
    popup?.close();
    throw error;
  }
};

export const clearAuthenticatedResumeBlob = (resumeUrl) => {
  revokeCachedBlob(resumeUrl);
  accessMetaCache.delete(resumeUrl);
};
