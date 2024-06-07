const apiUrl = 'https://smkvarqye6.execute-api.ap-southeast-2.amazonaws.com/api/api';

const poolData = {
    UserPoolId: 'ap-southeast-2_lTqg2n9qt',
    ClientId: '77groh9agrvonn6qdn9dfq4eg'
};

const userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

async function signUp(email, password, firstName, lastName) {
    const attributeList = [];

    const dataEmail = {
        Name: 'email',
        Value: email
    };
    const dataFirstName = {
        Name: 'given_name',
        Value: firstName
    };
    const dataLastName = {
        Name: 'family_name',
        Value: lastName
    };

    attributeList.push(new AmazonCognitoIdentity.CognitoUserAttribute(dataEmail));
    attributeList.push(new AmazonCognitoIdentity.CognitoUserAttribute(dataFirstName));
    attributeList.push(new AmazonCognitoIdentity.CognitoUserAttribute(dataLastName));

    return new Promise((resolve, reject) => {
        userPool.signUp(email, password, attributeList, null, function(err, result) {
            if (err) {
                console.error('Sign-up error:', err);
                reject(err);
            } else {
                console.log('Sign-up successful:', result);
                resolve(result.user);
            }
        });
    });
}

async function verifyUser(email, code) {
    const userData = {
        Username: email,
        Pool: userPool
    };

    const cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);

    return new Promise((resolve, reject) => {
        cognitoUser.confirmRegistration(code, true, function(err, result) {
            if (err) {
                console.error('Verification error:', err);
                reject(err);
            } else {
                console.log('Verification successful:', result);
                resolve(result);
            }
        });
    });
}

async function signIn(email, password) {
    const authenticationDetails = new AmazonCognitoIdentity.AuthenticationDetails({
        Username: email,
        Password: password
    });

    const userData = {
        Username: email,
        Pool: userPool
    };

    const cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);

    return new Promise((resolve, reject) => {
        cognitoUser.authenticateUser(authenticationDetails, {
            onSuccess: function(result) {
                console.log('Sign-in successful:', result);
                sessionStorage.setItem('cognitoUser', JSON.stringify(result));
                resolve(result);
            },
            onFailure: function(err) {
                console.error('Sign-in error:', err);
                reject(err);
            }
        });
    });
}

function isAuthenticated() {
    const cognitoUser = sessionStorage.getItem('cognitoUser');
    return cognitoUser != null;
}

function protectPage() {
    if (!isAuthenticated() && !window.location.pathname.endsWith("signup.html") && !window.location.pathname.endsWith("signin.html") && !window.location.pathname.endsWith("verify.html") && !window.location.pathname.endsWith("subscribe.html")) {
        window.location.href = 'signin.html';
    }
}

async function uploadImage(imageFile, imageName, userEmail) {
    const reader = new FileReader();
    reader.readAsDataURL(imageFile);
    reader.onload = async function() {
        const base64Image = reader.result.split(',')[1];
        const cognitoUser = JSON.parse(sessionStorage.getItem('cognitoUser'));

        if (!cognitoUser || !cognitoUser.idToken || !cognitoUser.idToken.jwtToken) {
            console.error('User is not authenticated');
            throw new Error('User is not authenticated');
        }

        const jwtToken = cognitoUser.idToken.jwtToken;
        const payload = {
            user_email: userEmail,
            image: base64Image,
            image_name: imageName
        };

        console.log('Payload:', payload); // Log payload for debugging

        const response = await fetch(`${apiUrl}/upload_image`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': jwtToken
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json();  // Get error response body
            console.error('Upload failed:', errorData);
            throw new Error('Upload failed: ' + (errorData.message || response.statusText));
        }

        return await response.json();
    };
}

async function queryImagesByTags(tags) {
    const response = await fetch(`${apiUrl}/search`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tags })
    });

    if (!response.ok) {
        const errorData = await response.json();
        console.error('Query failed:', errorData);
        throw new Error('Query failed: ' + (errorData.error || response.statusText));
    }

    const data = await response.json();
    return data; // 返回解析后的JSON数据
}

async function queryFullSizeImage(thumbnailUrl) {
    const response = await fetch(`${apiUrl}/thumbnail?thumbnail_url=${encodeURIComponent(thumbnailUrl)}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        const errorData = await response.json();
        console.error('Query failed:', errorData);
        throw new Error('Query failed: ' + (errorData.error || response.statusText));
    }

    const data = await response.json();
    return data.full_image_url; // Get full image URL
}

async function deleteImage(url) {
    const cognitoUser = JSON.parse(sessionStorage.getItem('cognitoUser'));

    if (!cognitoUser || !cognitoUser.idToken || !cognitoUser.idToken.jwtToken) {
        console.error('User is not authenticated');
        throw new Error('User is not authenticated');
    }

    const jwtToken = cognitoUser.idToken.jwtToken;
    const payload = {
        image_url: url
    };

    const response = await fetch(`${apiUrl}/delete_image`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': jwtToken
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        const errorData = await response.json();  // Get error response body
        console.error('Delete failed:', errorData);
        throw new Error('Delete failed: ' + (errorData.message || response.statusText));
    }

    return await response.json();
}

async function subscribeToTags(user_email, tags) {
    const cognitoUser = JSON.parse(sessionStorage.getItem('cognitoUser'));

    if (!cognitoUser || !cognitoUser.idToken || !cognitoUser.idToken.jwtToken) {
        console.error('User is not authenticated');
        throw new Error('User is not authenticated');
    }

    const jwtToken = cognitoUser.idToken.jwtToken;
    const payload = {
        user_email: user_email,
        subscribed_tags: tags
    };

    const response = await fetch(`${apiUrl}/subscribe`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': jwtToken
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        const errorData = await response.json();  // Get error response body
        console.error('Subscription failed:', errorData);
        throw new Error('Subscription failed: ' + (errorData.message || response.statusText));
    }

    return await response.json();
}

document.addEventListener("DOMContentLoaded", function() {
    protectPage();

    const mainContent = document.getElementById("main-content");
    const authStatus = document.getElementById("auth-status");

    if (authStatus && isAuthenticated()) {
        authStatus.innerHTML = `<p>You are logged in.</p>`;
    } else if (authStatus) {
        authStatus.innerHTML = `<p>You are not logged in.</p>`;
    }

    if (window.location.pathname.endsWith("signin.html")) {
        const signinForm = document.getElementById('signin-form');
        if (signinForm) {
            signinForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                console.log('Submitting sign-in form', { email, password });
                try {
                    const result = await signIn(email, password);
                    console.log('Sign-in successful', result);
                    document.getElementById('signin-result').innerText = 'Signed in successfully.';
                    window.location.href = 'index.html';
                } catch (error) {
                    console.error('Sign-in error:', error);
                    document.getElementById('signin-result').innerText = 'Error signing in: ' + error.message;
                }
            });
        }
    } else if (window.location.pathname.endsWith("signup.html")) {
        const signupForm = document.getElementById('signup-form');
        if (signupForm) {
            signupForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                const firstName = document.getElementById('first-name').value;
                const lastName = document.getElementById('last-name').value;
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                try {
                    const result = await signUp(email, password, firstName, lastName);
                    document.getElementById('signup-result').innerText = 'Signed up successfully. Please check your email to verify your account.';
                    window.location.href = 'verify.html';
                } catch (error) {
                    console.error('Sign-up error:', error);
                    document.getElementById('signup-result').innerText = 'Error signing up: ' + error.message;
                }
            });
        }
    } else if (window.location.pathname.endsWith("verify.html")) {
        const verifyForm = document.getElementById('verify-form');
        if (verifyForm) {
            verifyForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                const email = document.getElementById('email').value;
                const code = document.getElementById('code').value;
                try {
                    const result = await verifyUser(email, code);
                    document.getElementById('verify-result').innerText = 'Verification successful. You can now sign in.';
                    window.location.href = 'signin.html';
                } catch (error) {
                    console.error('Verification error:', error);
                    document.getElementById('verify-result').innerText = 'Error verifying: ' + error.message;
                }
            });
        }
    } else if (window.location.pathname.endsWith("signout.html")) {
        const cognitoUser = userPool.getCurrentUser();
        if (cognitoUser) {
            cognitoUser.signOut();
            sessionStorage.removeItem('cognitoUser');
            document.getElementById('main-content').innerText = 'You have been signed out.';
            setTimeout(() => {
                window.location.href = 'signin.html';
            }, 2000);
        } else {
            window.location.href = 'signin.html';
        }
    } else if (window.location.pathname.endsWith("upload.html")) {
        const uploadForm = document.getElementById('upload-form');
        if (uploadForm) {
            uploadForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                const fileInput = document.getElementById('image');
                const imageFile = fileInput.files[0];
                const imageName = fileInput.files[0].name;
                const userEmail = JSON.parse(sessionStorage.getItem('cognitoUser')).idToken.payload.email;
                try {
                    const result = await uploadImage(imageFile, imageName, userEmail);
                    document.getElementById('upload-result').innerText = 'Image uploaded successfully.';
                } catch (error) {
                    console.error('Upload error:', error);
                    document.getElementById('upload-result').innerText = 'Error uploading image: ' + error.message;
                }
            });
        }
    } else if (window.location.pathname.endsWith("query.html")) {
        const queryForm = document.getElementById('query-form');
        if (queryForm) {
            queryForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                const tagsInput = document.getElementById('tags').value;
                const tags = tagsInput.split(',').map(tag => tag.trim());
                try {
                    const result = await queryImagesByTags(tags);
                    console.log('Query result:', result);
                    const resultsDiv = document.getElementById('results');
                    resultsDiv.innerHTML = '';
                    if (Array.isArray(result)) {
                        result.forEach(link => {
                            const img = document.createElement('img');
                            img.src = link;
                            img.alt = 'Image';
                            img.style.maxWidth = '200px';
                            img.style.margin = '10px';
                            resultsDiv.appendChild(img);
                        });
                    } else {
                        resultsDiv.innerText = 'Unexpected result format';
                    }
                } catch (error) {
                    console.error('Query error:', error);
                    document.getElementById('results').innerText = 'Error querying images: ' + error.message;
                }
            });
        }

        const thumbnailQueryForm = document.getElementById('thumbnail-query-form');
        if (thumbnailQueryForm) {
            thumbnailQueryForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                const thumbnailUrl = document.getElementById('thumbnail-url').value;
                try {
                    const result = await queryFullSizeImage(thumbnailUrl);
                    console.log('Query result:', result);
                    const resultsDiv = document.getElementById('thumbnail-result');
                    resultsDiv.innerHTML = '';
                    if (result.full_image_url) {
                        const img = document.createElement('img');
                        img.src = result.full_image_url;
                        img.alt = 'Full Size Image';
                        img.style.maxWidth = '400px';
                        img.style.margin = '10px';
                        resultsDiv.appendChild(img);
                    } else {
                        resultsDiv.innerText = 'Unexpected result format';
                    }
                } catch (error) {
                    console.error('Query error:', error);
                    document.getElementById('thumbnail-result').innerText = 'Error querying full size image: ' + error.message;
                }
            });
        }

        const imageQueryForm = document.getElementById('image-query-form');
        if (imageQueryForm) {
            imageQueryForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                const fileInput = document.getElementById('query-image');
                const imageFile = fileInput.files[0];

                if (!imageFile) {
                    alert("Please select an image file to upload.");
                    return;
                }

                const reader = new FileReader();
                reader.readAsDataURL(imageFile);
                reader.onload = async function() {
                    const base64Image = reader.result.split(',')[1];

                    try {
                        const response = await fetch(`${apiUrl}/baseimage`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ image: base64Image })
                        });

                        if (!response.ok) {
                            const errorData = await response.json();
                            console.error('Query failed:', errorData);
                            throw new Error('Query failed: ' + (errorData.error || response.statusText));
                        }

                        const data = await response.json();
                        const resultsDiv = document.getElementById('image-query-result');
                        resultsDiv.innerHTML = '';

                        if (Array.isArray(data.items) && data.items.length > 0) {
                            data.items.forEach(item => {
                                const img = document.createElement('img');
                                img.src = item.thumbnail_url; // Assuming the response contains thumbnail_url for each item
                                img.alt = 'Image';
                                img.style.maxWidth = '200px';
                                img.style.margin = '10px';
                                resultsDiv.appendChild(img);
                            });
                        } else {
                            resultsDiv.innerText = 'No matching images found.';
                        }
                    } catch (error) {
                        console.error('Query error:', error);
                        document.getElementById('image-query-result').innerText = 'Error querying images: ' + error.message;
                    }
                };
            });
        }
    }

    if (window.location.pathname.endsWith("subscribe.html")) {
        const subscribeForm = document.getElementById('subscribe-form');
        if (subscribeForm) {
            subscribeForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                const emailInput = document.getElementById('email').value;
                const tagsInput = document.getElementById('tags').value;
                const tags = tagsInput.split(',').map(tag => tag.trim());
                try {
                    const result = await subscribeToTags(emailInput, tags);
                    console.log('Subscription result:', result);
                    document.getElementById('subscribe-result').innerText = 'Subscription updated successfully.';
                } catch (error) {
                    console.error('Subscription error:', error);
                    document.getElementById('subscribe-result').innerText = 'Error subscribing to tags: ' + error.message;
                }
            });
        }
    }

    const urlParams = new URLSearchParams(window.location.search);
    const imageUrl = urlParams.get('image-url');
    const deleteResult = document.getElementById('delete-result');

    if (imageUrl && deleteResult) {
        deleteImage(imageUrl).then(result => {
            console.log('Delete successful:', result);
            deleteResult.innerText = 'Image deleted successfully.';
        }).catch(error => {
            console.error('Delete error:', error);
            deleteResult.innerText = 'Error deleting image: ' + error.message;
        });
    }
});