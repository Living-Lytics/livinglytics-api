// Mock Base44 client for local development
// This prevents redirects to Base44 login page

export const base44 = {
  auth: {
    redirectToLogin: () => {
      // For now, just redirect to a signup page or show alert
      console.log('Signup/Login would happen here - redirecting to /contact');
      window.location.href = '/contact';
    },
    isAuthenticated: () => false,
    getUser: () => null
  },
  integrations: {
    Core: {
      InvokeLLM: () => console.log('LLM integration placeholder'),
      SendEmail: () => console.log('Email integration placeholder'),
      UploadFile: () => console.log('Upload integration placeholder'),
      GenerateImage: () => console.log('Image generation placeholder'),
      ExtractDataFromUploadedFile: () => console.log('Extract data placeholder'),
      CreateFileSignedUrl: () => console.log('Signed URL placeholder'),
      UploadPrivateFile: () => console.log('Private upload placeholder'),
    }
  }
};

// For backwards compatibility
export const createClient = () => base44;
