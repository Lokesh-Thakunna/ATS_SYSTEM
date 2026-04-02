import api from '../services/api';

const blobUrlCache = new Map();

const revokeCachedBlob = (resumeUrl) => {
  const cached = blobUrlCache.get(resumeUrl);
  if (cached) {
    URL.revokeObjectURL(cached);
    blobUrlCache.delete(resumeUrl);
  }
};

export const getAuthenticatedResumeBlobUrl = async (resumeUrl, { forceRefresh = false } = {}) => {
  if (!resumeUrl) {
    throw new Error('Resume URL is missing');
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

    const blobUrl = await getAuthenticatedResumeBlobUrl(resumeUrl, { forceRefresh: true });

    if (popup) {
      popup.location.replace(blobUrl);
    } else {
      window.open(blobUrl, '_blank', 'noopener,noreferrer');
    }

    return blobUrl;
  } catch (error) {
    popup?.close();
    throw error;
  }
};

export const clearAuthenticatedResumeBlob = (resumeUrl) => {
  revokeCachedBlob(resumeUrl);
};
