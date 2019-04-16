const emoji = require('base64-emoji');
const cheerio = require('cheerio');
const { Gmail } = require('gmail-js');
const gmail = new Gmail();

const nuBoxGmail = {
  init: () => {
    // Ask for user Approval
    if (gmail.check.is_new_gui()) {
      nuBox.approve();
    }

    gmail.observe.on('compose', function(compose, type) {
      // Add button to the "Compose Email".
      const composeRef = gmail.dom.composes()[0];

      gmail.tools.add_compose_button(composeRef, 'Encrypt (nuBox)', () => {
        nuBoxGmail.encryptEmail(composeRef);
      }, 'nubox-r-c-btn-r');

      gmail.tools.add_compose_button(composeRef, 'Decrypt (nuBox)', () => {
        nuBoxGmail.decryptEmail(composeRef);
      }, 'nubox-r-c-btn-r');
    });
  },

  decryptEmail: async (composeRef) => {
    // Use the email subject as label.
    const label = composeRef.subject();
    if (label === undefined || label === null || label.trim().length === 0) {
      gmail.tools.add_modal_window('Decrypt with nuBox', 'Subject cannot be empty!',
        () => {
            gmail.tools.remove_modal_window();
        });
      return;
    }

    // Retrieve the email body.
    // Handle Google emoijis (which are loaded only if page is refreshed or email is sent)
    let body = composeRef.body();
    const $ = cheerio.load(body);
    if ($('img[goomoji]').length > 0) {
      body = $('img[goomoji]').map((i, el) => $(el).attr('alt')).get().join('');
    }

    try {
      // Decrypt the body with NuCypher.
      const encrypted = emoji.decode(body).toString();
      const decrypted = await nuBox.decrypt(encrypted, label);
      composeRef.body(Buffer.from(decrypted, 'base64').toString());

    } catch (err) {
      console.log(err);
      composeRef.body(body);

      gmail.tools.add_modal_window('Decrypt with nuBox', 'Something went wrong while decrypting!',
        () => {
            gmail.tools.remove_modal_window();
        });
    }
  },

  encryptEmail: async (composeRef) => {
    // Use the email subject as label.
    const label = composeRef.subject();
    if (label === undefined || label === null || label.trim().length === 0) {
      gmail.tools.add_modal_window('Encrypt with nuBox', 'Subject cannot be empty!',
        () => {
            gmail.tools.remove_modal_window();
        });
      return;
    }

    // Retrieve the email body.
    const body = composeRef.body();

    try {
      // Encrypt the body with NuCypher.
      const encrypted = await nuBox.encrypt(body, label);

      // Encode the text to emojis!
      composeRef.body(emoji.encode(encrypted).toString());

      // Grant approval for this user (so he/she can read his own emails).
      const bob = await nuBox.getBobKeys();
      await nuBox.grant(label, bob.bek, bob.bvk, '3017-01-01 00:00:00', true);

    } catch (err) {
      console.log(err);
      composeRef.body(body);

      gmail.tools.add_modal_window('Encrypt with nuBox', 'Something went wrong while encrypting!',
        () => {
            gmail.tools.remove_modal_window();
        });
    }
  },

  getUserEmail: () => {
    return gmail.get.user_email();
  },
};

nuBoxGmail.init();

module.exports = nuBoxGmail;
