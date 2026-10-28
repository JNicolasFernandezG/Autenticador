const API_BASE =
  (import.meta as any).env?.VITE_API_URL ||
  (typeof window !== 'undefined' && window.location.port === '5173'
    ? 'http://localhost:8000'
    : '');


export interface ServicioCatalogo {
  clave: string;
  nombre: string;
  descripcion: string;
  url_base: string;
  ruta_magic_link?: string;
  color: string;
  activo: boolean;
}

export interface MagicLinkServicioItem {
  clave: string;
  nombre: string;
  urlBase: string;
  accessUrl: string;
  habilitado: boolean;
}

export interface EstadoUsuario {
  id: number;
  codigo: string;
  nombre: string;
  descripcion: string;
  permite_login: boolean;
  color: string;
  habilitado: boolean;
}

export interface Usuario {
  id: number;
  name: string;
  email: string;
  codigoAcceso: string;
  tipoUsuario: number;
  activo: boolean;
  estadoId: number;
  estadoCodigo: string;
  servicios: Record<string, boolean>;
  dateStart?: string | null;
  dateEnd?: string | null;
}

export interface PaginatedUsuarios {
  total: number;
  skip: number;
  limit: number;
  items: Usuario[];
}

function getHeaders(token?: string | null): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || data.message || `Error HTTP ${res.status}`);
  }
  return data as T;
}

export const api = {
  async loginAdmin(email: string, password: string) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ email, password }),
    });
    return handleResponse<{
      success: boolean;
      token: string;
      user: Usuario;
      message: string;
    }>(res);
  },

  async getUsuarios(
    token: string,
    params: {
      limit?: number;
      skip?: number;
      nombre?: string;
      tipoUsuario?: number;
      activo?: boolean;
      servicio?: string;
      orden?: string;
    }
  ) {
    const qs = new URLSearchParams();
    if (params.limit !== undefined) qs.set('limit', String(params.limit));
    if (params.skip !== undefined) qs.set('skip', String(params.skip));
    if (params.nombre) qs.set('nombre', params.nombre);
    if (params.tipoUsuario !== undefined) qs.set('tipoUsuario', String(params.tipoUsuario));
    if (params.activo !== undefined) qs.set('activo', String(params.activo));
    if (params.servicio) qs.set('servicio', params.servicio);
    if (params.orden) qs.set('orden', params.orden);

    const res = await fetch(`${API_BASE}/usuario?${qs.toString()}`, {
      headers: getHeaders(token),
    });
    return handleResponse<PaginatedUsuarios>(res);
  },

  async crearUsuario(
    token: string,
    payload: {
      name: string;
      email: string;
      codigoAcceso?: string;
      tipoUsuario: number;
      activo: boolean;
      servicios: Record<string, boolean>;
    }
  ) {
    const res = await fetch(`${API_BASE}/usuario`, {
      method: 'POST',
      headers: getHeaders(token),
      body: JSON.stringify(payload),
    });
    return handleResponse<Usuario>(res);
  },

  async toggleActivo(token: string, userId: number) {
    const res = await fetch(`${API_BASE}/usuario/${userId}/toggle-activo`, {
      method: 'PATCH',
      headers: getHeaders(token),
    });
    return handleResponse<{ success: boolean; message: string; activo: boolean }>(res);
  },

  async eliminarUsuario(token: string, userId: number) {
    const res = await fetch(`${API_BASE}/usuario/${userId}`, {
      method: 'DELETE',
      headers: getHeaders(token),
    });
    return handleResponse<{ success: boolean; message: string }>(res);
  },

  async toggleServicio(token: string, userId: number, servicioClave: string) {
    const res = await fetch(
      `${API_BASE}/usuario/${userId}/toggle-servicio/${encodeURIComponent(servicioClave)}`,
      {
        method: 'PATCH',
        headers: getHeaders(token),
      }
    );
    return handleResponse<{
      success: boolean;
      message: string;
      servicio: string;
      habilitado: boolean;
      servicios: Record<string, boolean>;
    }>(res);
  },

  async cambiarEstado(token: string, userId: number, estadoId: number) {
    const res = await fetch(`${API_BASE}/usuario/${userId}/estado`, {
      method: 'PATCH',
      headers: getHeaders(token),
      body: JSON.stringify({ estado_id: estadoId }),
    });
    return handleResponse<{
      success: boolean;
      message: string;
      estado_id: number;
      estado_codigo: string;
      activo: boolean;
    }>(res);
  },

  async generarMagicLink(token: string, userId: number) {
    const res = await fetch(`${API_BASE}/usuario/${userId}/magic-link`, {
      method: 'POST',
      headers: getHeaders(token),
    });
    return handleResponse<{
      success: boolean;
      token: string;
      accessUrl: string;
      codigoAcceso: string;
      activo: boolean;
      magicLinks: Record<string, MagicLinkServicioItem>;
      magicLinksList: MagicLinkServicioItem[];
      message: string;
    }>(res);
  },

  async getServiciosCatalogo(token: string) {
    const res = await fetch(`${API_BASE}/usuario/servicios/catalogo`, {
      headers: getHeaders(token),
    });
    return handleResponse<{ success: boolean; servicios: ServicioCatalogo[] }>(res);
  },

  async crearServicioCatalogo(
    token: string,
    payload: {
      clave: string;
      nombre: string;
      url_base: string;
      ruta_magic_link?: string;
      descripcion?: string;
      color?: string;
    }
  ) {
    const res = await fetch(`${API_BASE}/usuario/servicios/catalogo`, {
      method: 'POST',
      headers: getHeaders(token),
      body: JSON.stringify(payload),
    });
    return handleResponse<{ success: boolean; message: string; servicio: ServicioCatalogo }>(res);
  },

  async actualizarServicioCatalogo(
    token: string,
    clave: string,
    payload: {
      nombre?: string;
      url_base?: string;
      ruta_magic_link?: string;
      descripcion?: string;
    }
  ) {
    const res = await fetch(
      `${API_BASE}/usuario/servicios/catalogo/${encodeURIComponent(clave)}`,
      {
        method: 'PATCH',
        headers: getHeaders(token),
        body: JSON.stringify(payload),
      }
    );
    return handleResponse<{ success: boolean; message: string; servicio: ServicioCatalogo }>(res);
  },

  async getEstadosCatalogo(token: string) {
    const res = await fetch(`${API_BASE}/usuario/estados/catalogo`, {
      headers: getHeaders(token),
    });
    return handleResponse<{ success: boolean; estados: EstadoUsuario[] }>(res);
  },

  async simularValidacionServicio(payload: {
    email?: string;
    codigoAcceso?: string;
    servicio: string;
  }) {
    const res = await fetch(`${API_BASE}/auth/validar-acceso`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });
    return handleResponse<{
      success: boolean;
      allowed: boolean;
      message: string;
      token?: string;
      user?: Usuario;
    }>(res);
  },
  async generarTicketSSO(token: string, servicioDestino: string = 'mayoresactualizaciones') {
    const res = await fetch(`${API_BASE}/auth/sso/create-ticket`, {
      method: 'POST',
      headers: getHeaders(token),
      body: JSON.stringify({ servicio: servicioDestino }),
    });
    return handleResponse<{
      success: boolean;
      ticket: string;
      expiresInSeconds: number;
      servicio: string;
    }>(res);
  },

  async consumirTicketSSO(ticket: string, servicioSolicitante: string = 'autenticador') {
    const res = await fetch(`${API_BASE}/auth/sso/consume-ticket`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ ticket, servicio: servicioSolicitante }),
    });
    return handleResponse<{
      success: boolean;
      token: string;
      user: Usuario;
      message: string;
    }>(res);
  },
};
