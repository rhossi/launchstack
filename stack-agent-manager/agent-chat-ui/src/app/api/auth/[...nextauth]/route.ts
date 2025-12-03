// app/api/auth/[...nextauth]/route.ts
import NextAuth from "next-auth";

// Get environment variables with defaults for build time
const OCI_ISSUER = process.env.OCI_ISSUER || '';
const OCI_CLIENT_ID = process.env.OCI_CLIENT_ID || '';
const OCI_CLIENT_SECRET = process.env.OCI_CLIENT_SECRET || '';
const NEXTAUTH_SECRET = process.env.NEXTAUTH_SECRET || '';

const handler = NextAuth({
  debug: true,
  pages: {
    signIn: "/login",
  },
  providers: [
    {
      id: "oci",
      name: "OCI Identity Domain",
      type: "oauth",
      wellKnown: `${OCI_ISSUER}/.well-known/openid-configuration`,
      authorization: { params: { scope: "openid email profile" } },
      clientId: OCI_CLIENT_ID,
      clientSecret: OCI_CLIENT_SECRET,
      idToken: true,
      checks: ["pkce", "state"],
      client: {
        token_endpoint_auth_method: "client_secret_post",
      },
      profile(profile) {
        return {
          id: profile.sub,
          name: profile.name ?? profile.preferred_username,
          email: profile.email,
          image: profile.picture,
        };
      },
    },
  ],
  callbacks: {
    async jwt({ token, account, profile, user }) {
      // Persist the access_token and id_token to the JWT
      if (account) {
        token.accessToken = account.access_token;
        token.idToken = account.id_token;
      }
      
      // Store profile data in the token on first sign in
      if (profile) {
        const ociProfile = profile as any;
        token.name = ociProfile.name ?? ociProfile.preferred_username;
        token.email = ociProfile.email;
        token.picture = ociProfile.picture;
      }
      
      // Also try to get from user object if available
      if (user) {
        token.name = token.name || user.name;
        token.email = token.email || user.email;
        token.picture = token.picture || user.image;
      }
      
      // If we still don't have user info but have an idToken, decode it to get user info
      if ((!token.name || !token.email) && token.idToken) {
        try {
          // Decode the JWT idToken (it's base64 encoded)
          const idToken = token.idToken as string;
          const payload = JSON.parse(
            Buffer.from(idToken.split('.')[1], 'base64').toString()
          );
          
          token.name = payload.user_displayname || payload.name || token.sub;
          token.email = payload.sub || payload.email;
          token.picture = payload.picture;
          
          console.log("JWT callback - decoded from idToken:", { 
            name: token.name, 
            email: token.email, 
            picture: token.picture 
          });
        } catch (e) {
          console.error("Failed to decode idToken:", e);
        }
      }
      
      return token;
    },
    async session({ session, token }) {
      // Send properties to the client, like an access_token and user info
      session.accessToken = token.accessToken as string;
      
      // Populate user info from token (initialize user object if it doesn't exist)
      session.user = {
        name: (token.name as string) || undefined,
        email: (token.email as string) || undefined,
        image: (token.picture as string) || undefined,
      };
      
      return session;
    },
  },
});

export { handler as GET, handler as POST };