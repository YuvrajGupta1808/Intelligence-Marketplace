'use server';

export const signUpWithEmail = async (_data: SignUpFormData) => {
    return { success: true, data: null };
};

export const signInWithEmail = async (_data: SignInFormData) => {
    return { success: true, data: null };
};

export const signOut = async () => {
    return { success: true };
};
