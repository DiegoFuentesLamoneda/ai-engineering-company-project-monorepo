// Contrato de las cuentas de la API propia (services/api) en TypeScript:
// dominios auth, users y profiles. Ver services/api/README.md.

export type Role = "admin" | "manager" | "user";

/** Nombre y datos de contacto. Todos opcionales: null es "sin dato". */
export interface ProfileFields {
  name: string | null;
  phone: string | null;
  address: string | null;
}

/** El perfil vinculado a una cuenta (uno por usuario). */
export interface Profile extends ProfileFields {
  id: string;
  user_id: string;
}

/**
 * PUT /profiles/me: solo cambian los campos enviados; uno a null se borra.
 * Partial porque un campo ausente se queda como estaba.
 */
export type ProfileUpdate = Partial<ProfileFields>;

/** POST /auth/login: la respuesta estándar de OAuth2. */
export interface Token {
  access_token: string;
  token_type: "bearer";
  /** Segundos de validez. */
  expires_in: number;
}

/** GET /auth/me: quién soy, con qué rol y mi perfil. */
export interface Me {
  id: string;
  email: string;
  role: Role;
  profile: Profile;
}

/** POST /users (registro): credenciales y, opcionalmente, el perfil inicial. */
export interface RegisterInput extends Partial<ProfileFields> {
  email: string;
  password: string;
}

/** Respuesta de POST /users: la cuenta creada, sin contraseña, y su perfil. */
export interface UserCreated {
  id: string;
  email: string;
  role: Role;
  is_active: boolean;
  created_at: string;
  profile: Profile;
}
